"""Download each Epoch dataset to data/raw/, then write a cleaned copy to data/processed/."""

import time
from pathlib import Path

import polars as pl

from . import download
from .datasets import EpochDataset

ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = ROOT / "data" / "raw" / "epoch_ai"
CLEAN_DIR = ROOT / "data" / "processed" / "epoch_ai"
DELAY_S = 1.5  # be polite between network calls


def _clean_csv(src: Path, out: Path) -> int:
    """Light clean: strip column names, drop all-null columns. Returns row count."""
    df = pl.read_csv(src, infer_schema_length=20000, ignore_errors=True, truncate_ragged_lines=True)
    df = df.rename({c: c.strip() for c in df.columns})
    keep = [c for c in df.columns if df[c].null_count() < df.height]
    df = df.select(keep) if keep else df
    out.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(out)
    return df.height


def _fetch_raw(ds: EpochDataset, raw_dir: Path) -> int:
    """Download/extract raw files for a dataset. Returns total bytes downloaded."""
    if ds.kind == "csv":
        return download.download(ds.download_url, raw_dir / Path(ds.download_url).name)
    if ds.kind == "zip":
        zip_path = raw_dir / Path(ds.download_url).name
        n = download.download(ds.download_url, zip_path)
        download.extract_zip(zip_path, raw_dir)
        return n
    if ds.kind == "github":
        download.fetch_repo(ds.download_url, raw_dir)
        return sum(p.stat().st_size for p in raw_dir.rglob("*") if p.is_file())
    raise ValueError(f"unknown kind {ds.kind!r}")


def ingest(ds: EpochDataset) -> dict:
    """Fetch + clean one dataset. Never raises; returns a result row."""
    raw_dir = RAW_DIR / ("github" if ds.kind == "github" else "") / ds.slug
    result = {"slug": ds.slug, "name": ds.name, "status": "ok", "bytes": 0,
              "csv_files": 0, "rows": 0, "note": ""}
    try:
        result["bytes"] = _fetch_raw(ds, raw_dir)
        # Clean every CSV found under the raw dir.
        csvs = sorted(p for p in raw_dir.rglob("*.csv"))
        for src in csvs:
            stem = src.stem if len(csvs) == 1 else f"{ds.slug}__{src.stem}"
            out = CLEAN_DIR / f"{stem}.csv"
            if ds.kind == "github":
                out = CLEAN_DIR / "github" / f"{ds.slug}__{src.stem}.csv"
            try:
                result["rows"] += _clean_csv(src, out)
                result["csv_files"] += 1
            except Exception as e:  # noqa: BLE001 - keep going on a bad file
                result["note"] += f"clean {src.name}: {e}; "
        others = [p.suffix for p in raw_dir.rglob("*") if p.is_file() and p.suffix in {".json", ".parquet"}]
        if result["csv_files"] == 0 and not others:
            result["status"] = "empty"
            result["note"] += "no CSV/JSON/parquet data files found; "
    except Exception as e:  # noqa: BLE001 - one dataset failing shouldn't stop the rest
        result["status"] = "failed"
        result["note"] = str(e)
    return result


def run(slugs: list[EpochDataset]) -> list[dict]:
    results = []
    for i, ds in enumerate(slugs):
        print(f"[{i + 1}/{len(slugs)}] {ds.slug} ({ds.kind}) ...", flush=True)
        results.append(ingest(ds))
        if i < len(slugs) - 1:
            time.sleep(DELAY_S)
    return results
