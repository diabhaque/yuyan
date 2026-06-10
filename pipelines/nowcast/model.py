"""Step 4 — nowcast model. Per component: build supply/demand/price/macro/trend estimates
from real external scalars (config.py, sourced in sources.py) applied to the Epoch trend
baseline, then reconcile (don't add suppliers+buyers — two views of one spend)."""

import polars as pl

from . import config

B = 1e9  # report in USD billions


def _qkey(q: str) -> int:
    qn, yr = q.split(" ")
    return int(yr) * 4 + int(qn[1]) - 1


def _num(c):
    return pl.col(c).cast(pl.String).str.replace_all(r"[$,%]", "").cast(pl.Float64, strict=False)


def _quarterly_totals() -> pl.DataFrame:
    """4-designer per-component totals (USD) by quarter, chronological."""
    df = pl.read_csv(config.BASE_CSV, infer_schema_length=20000, ignore_errors=True,
                     truncate_ragged_lines=True).filter(
        pl.col("Designer").is_in(config.TARGET_DESIGNERS))
    df = df.with_columns([_num(col).alias(comp) for comp, col in config.COST_COL.items()])
    g = df.group_by("Quarter").agg([pl.col(c).sum().alias(c) for c in config.COMPONENTS])
    return g.with_columns(pl.col("Quarter").map_elements(_qkey, return_dtype=pl.Int64).alias("_k")).sort("_k")


def _estimates(comp: str, L4: float, median_qoq: float, scenario: str) -> dict:
    """All estimates for one component as full-quarter levels (USD)."""
    trend = L4 * (1 + median_qoq)
    supply = L4 * (1 + config.SUPPLY_QOQ[comp][scenario])
    demand = L4 * (1 + config.DEMAND_QOQ[comp][scenario])
    if comp == "Memory":  # explicit price x volume decomposition
        price = L4 * (1 + config.VOLUME_QOQ[scenario]) * (1 + config.PRICE_QOQ[scenario])
    else:
        price = trend  # no memory-style price index for these
    macro = trend * config.MACRO_SCALER[scenario]
    w = config.WEIGHTS
    reconciled = (w["supply"] * supply + w["price"] * price + w["trend"] * trend
                  + w["macro"] * macro + w["demand"] * demand)
    return {"trend": trend, "supply": supply, "demand": demand, "price": price,
            "macro": macro, "reconciled": reconciled}


def run() -> dict:
    config.PROC_DIR.mkdir(parents=True, exist_ok=True)
    tot = _quarterly_totals()
    tot.drop("_k").with_columns([(pl.col(c) / B) for c in config.COMPONENTS]).write_csv(
        config.PROC_DIR / "nowcast_history.csv")  # 4-designer totals ($B) per quarter
    complete = tot.filter(pl.col("Quarter") != config.TARGET_QUARTER)

    rows, detail = [], []
    for comp in config.COMPONENTS:
        series = complete[comp].to_list()
        L4 = complete.filter(pl.col("Quarter") == config.LAST_COMPLETE)[comp][0]
        qoq = [series[i] / series[i - 1] - 1 for i in range(1, len(series))]
        median_qoq = sorted(qoq)[len(qoq) // 2]
        partial = tot.filter(pl.col("Quarter") == config.TARGET_QUARTER)[comp]
        partial = (partial[0] if partial.len() else 0.0)

        base = _estimates(comp, L4, median_qoq, "base")
        low = _estimates(comp, L4, median_qoq, "low")
        high = _estimates(comp, L4, median_qoq, "high")
        rows.append({
            "component": comp,
            "partial_actual": partial / B,
            "supply_side": base["supply"] / B,
            "demand_side": base["demand"] / B,
            "price_adjusted": base["price"] / B,
            "macro_calibrated": base["macro"] / B,
            "trend_only": base["trend"] / B,
            "reconciled_base": base["reconciled"] / B,
            "low": low["reconciled"] / B,
            "high": high["reconciled"] / B,
            "confidence": config.CONFIDENCE[comp],
        })
        for est in ["trend", "supply", "demand", "price", "macro", "reconciled"]:
            detail.append({"component": comp, "estimate": est, "value_b": base[est] / B})

    out = pl.DataFrame(rows)
    total = {"component": "TOTAL", "confidence": "-"}
    for col in ["partial_actual", "supply_side", "demand_side", "price_adjusted",
                "macro_calibrated", "trend_only", "reconciled_base", "low", "high"]:
        total[col] = out[col].sum()
    out = pl.concat([out, pl.DataFrame([total])], how="diagonal_relaxed")

    out.write_csv(config.PROC_DIR / "nowcast_q1_2026.csv")
    pl.DataFrame(detail).write_csv(config.PROC_DIR / "nowcast_estimates_detail.csv")

    t = out.filter(pl.col("component") == "TOTAL").row(0, named=True)
    print(f"  Q1 2026 reconciled base TOTAL: ${t['reconciled_base']:.1f}B "
          f"(low ${t['low']:.1f}B - high ${t['high']:.1f}B); trend-only ${t['trend_only']:.1f}B")
    return {"total": t, "table": out}
