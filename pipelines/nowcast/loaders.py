"""Step 2 — retrieve raw -> data/raw/nowcast/. Writes the evidence registry to disk and
fetches the one cleanly-downloadable machine series (FRED). Other figures are transcribed
from cited official releases in sources.py (URL + as_of), kept here as the raw record."""

import json

import polars as pl

from ..epoch_ai import download
from . import config
from .sources import FRED_CSV_URL, FRED_SERIES, NOT_OBTAINED, SOURCES


def fetch() -> None:
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)

    # One subfolder per source with its transcribed record (traceable to URL + as_of).
    for s in SOURCES:
        d = config.RAW_DIR / s["name"].replace(" ", "_").replace("/", "_")
        d.mkdir(parents=True, exist_ok=True)
        (d / "record.json").write_text(json.dumps(s, indent=2))

    # FRED is a real machine-readable download (free, no key).
    fred_note = "ok"
    try:
        download.download(FRED_CSV_URL, config.RAW_DIR / "FRED_IPG3344S" / f"{FRED_SERIES}.csv")
    except Exception as e:  # noqa: BLE001 - fall back to trend if unreachable
        fred_note = f"FAILED: {e}"
    print(f"  FRED {FRED_SERIES}: {fred_note}")

    # Retrieval manifest.
    man = pl.DataFrame([
        {"source": s["name"], "family": s["family"], "type": s["confidence"],
         "new_info": s.get("new_info", ""), "targets": ",".join(s["targets"]),
         "period": s["period"], "url": s["url"], "as_of": s["as_of"],
         "component": ",".join(s["component"])}
        for s in SOURCES
    ])
    man.write_csv(config.RAW_DIR / "manifest.csv")
    (config.RAW_DIR / "not_obtained.txt").write_text("\n".join(NOT_OBTAINED))
    print(f"  wrote {man.height} source records + manifest to {config.RAW_DIR}")
