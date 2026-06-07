"""Pipeline base class + CSV storage with point-in-time upsert."""

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

CORE = ["TS", "primary_id", "value", "TS_RECORDED"]
REQUIRED = ["TS", "primary_id", "value"]  # what fetch() must supply
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class Pipeline(ABC):
    name: str  # registry name + output filename
    key_columns = ["TS", "primary_id"]  # upsert key

    @abstractmethod
    def fetch(self) -> pd.DataFrame:
        """Return rows with TS, primary_id, value (+ optional extra columns)."""

    def run(self) -> pd.DataFrame:
        df = self.fetch()
        missing = [c for c in REQUIRED if c not in df.columns]
        if missing:
            raise ValueError(f"{self.name}.fetch() missing columns: {missing}")
        df["TS_RECORDED"] = pd.Timestamp.now(tz="UTC").isoformat()

        DATA_DIR.mkdir(exist_ok=True)
        path = DATA_DIR / f"{self.name}.csv"
        combined = upsert(df, path, self.key_columns)
        combined.to_csv(path, index=False)
        print(f"{self.name}: {len(df)} fetched, {len(combined)} rows total -> {path}")
        return combined


def upsert(new: pd.DataFrame, path: Path, key: list[str]) -> pd.DataFrame:
    """Merge `new` into the CSV at `path` on `key`; updated rows get a fresh TS_RECORDED."""
    if path.exists():
        old = pd.read_csv(path)
        # new rows win on key collisions, carrying their fresh TS_RECORDED
        combined = pd.concat([old, new]).drop_duplicates(subset=key, keep="last")
    else:
        combined = new
    return combined.sort_values(key).reset_index(drop=True)
