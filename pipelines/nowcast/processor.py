"""Step 3 — tidy raw -> data/processed/nowcast/. Builds the company/price/macro tables
and a committed source registry in datasources/nowcast_sources.csv."""

import polars as pl

from . import config
from .sources import FRED_SERIES, SOURCES

DATASOURCES = config.ROOT / "datasources" / "nowcast_sources.csv"


def _fred_recent_yoy() -> str:
    path = config.RAW_DIR / "FRED_IPG3344S" / f"{FRED_SERIES}.csv"
    if not path.exists():
        return "n/a (FRED not fetched)"
    df = pl.read_csv(path, ignore_errors=True).drop_nulls()
    val = df.columns[-1]
    df = df.with_columns(pl.col(val).cast(pl.Float64, strict=False)).drop_nulls(val)
    if df.height < 13:
        return "n/a (short series)"
    latest, prior = df[val][-1], df[val][-13]
    return f"{(latest / prior - 1) * 100:+.1f}% YoY (latest {df.columns[0]}={df[df.columns[0]][-1]})"


def process() -> None:
    config.PROC_DIR.mkdir(parents=True, exist_ok=True)

    company = [s for s in SOURCES if s["family"] == "A"]
    price = [s for s in SOURCES if s["family"] == "B"]
    macro = [s for s in SOURCES if s["family"] == "C"]

    def tidy(rows):
        return pl.DataFrame([
            {"source": s["name"], "metric": s["metric"], "value": s["value"],
             "period": s["period"], "component": ",".join(s["component"]),
             "confidence": s["confidence"], "url": s["url"], "as_of": s["as_of"], "note": s["note"]}
            for s in rows
        ])

    tidy(company).write_csv(config.PROC_DIR / "company.csv")
    tidy(price).write_csv(config.PROC_DIR / "price.csv")
    macro_df = tidy(macro)
    # Append the live FRED-derived figure as a structured macro row.
    macro_df = macro_df.with_columns(
        pl.when(pl.col("source") == "FRED IPG3344S").then(pl.lit(_fred_recent_yoy()))
        .otherwise(pl.col("value")).alias("value")
    )
    macro_df.write_csv(config.PROC_DIR / "macro.csv")

    # Committed registry (datasources/ convention).
    DATASOURCES.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame([
        {"source": s["name"], "family": s["family"], "type": s["confidence"],
         "period": s["period"], "url": s["url"], "as_of": s["as_of"],
         "component": ",".join(s["component"]), "metric": s["metric"], "value": s["value"]}
        for s in SOURCES
    ]).write_csv(DATASOURCES)
    print(f"  wrote company/price/macro tables -> {config.PROC_DIR}")
    print(f"  FRED IPG3344S: {_fred_recent_yoy()}")
    print(f"  registry -> {DATASOURCES}")
