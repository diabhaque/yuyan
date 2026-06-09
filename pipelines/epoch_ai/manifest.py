"""Write the datasources/epoch_ai.csv manifest from the dataset registry."""

from pathlib import Path

import polars as pl

from .datasets import ALL, LICENSE, EpochDataset

ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST = ROOT / "datasources" / "epoch_ai.csv"

PLAN = {
    "zip": "Download ZIP, extract CSV(s) to raw_data, clean to data",
    "csv": "Download CSV directly to raw_data, clean to data",
    "github": "Fetch repo tarball, copy data files to raw_data, clean CSVs to data",
}


def _human(n: int) -> str:
    x = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if x < 1024 or unit == "GB":
            return f"{x:.0f} {unit}" if unit == "B" else f"{x:.1f} {unit}"
        x /= 1024


def write(sizes: dict[str, int] | None = None) -> None:
    """sizes: slug -> bytes downloaded; omit for a pre-download manifest."""
    rows = []
    for d in ALL:  # type: EpochDataset
        size = sizes.get(d.slug) if sizes else None
        rows.append({
            "name": d.name,
            "slug": d.slug,
            "source_url": d.explorer_url,
            "download_url": d.download_url,
            "format": d.kind,
            "approx_size": _human(size) if size else "pending",
            "license": LICENSE,
            "citation": d.citation,
            "retrieval_plan": PLAN[d.kind],
        })
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(rows).write_csv(MANIFEST)
