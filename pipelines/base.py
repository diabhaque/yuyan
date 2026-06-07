"""Pipeline base class + CSV storage with point-in-time upsert."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

CORE = ["TS", "primary_id", "value", "TS_RECORDED"]
REQUIRED = ["TS", "primary_id", "value"]  # what fetch() must supply
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class Pipeline(ABC):
    name: str  # registry name + output filename
    key_columns = ["TS", "primary_id"]  # upsert key

    @abstractmethod
    def fetch(self) -> pl.DataFrame:
        """Return rows with TS, primary_id, value (+ optional extra columns)."""

    def run(self) -> pl.DataFrame:
        df = self.fetch()
        missing = [c for c in REQUIRED if c not in df.columns]
        if missing:
            raise ValueError(f"{self.name}.fetch() missing columns: {missing}")
        df = df.with_columns(pl.lit(datetime.now(timezone.utc).isoformat()).alias("TS_RECORDED"))

        DATA_DIR.mkdir(exist_ok=True)
        path = DATA_DIR / f"{self.name}.csv"
        combined = upsert(df, path, self.key_columns)
        combined.write_csv(path)
        print(f"{self.name}: {len(df)} fetched, {len(combined)} rows total -> {path}")
        return combined


def upsert(new: pl.DataFrame, path: Path, key: list[str]) -> pl.DataFrame:
    """Merge `new` into the CSV at `path` on `key`; updated rows get a fresh TS_RECORDED."""
    if path.exists():
        old = pl.read_csv(path)
        # new rows win on key collisions, carrying their fresh TS_RECORDED
        combined = pl.concat([old, new], how="vertical_relaxed").unique(subset=key, keep="last")
    else:
        combined = new
    return combined.sort(key)
