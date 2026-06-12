"""Nowcast/forecast model. Per component: build supply/demand/price/macro/analyst/trend
estimates from real external scalars (config.py, sourced in sources.py) applied to the
prior-quarter level, then reconcile (don't add suppliers+buyers — two views of one spend).
Targets can chain: Q2 2026 forecast uses the Q1 2026 nowcast output as its base level."""

from statistics import mean, pstdev

import polars as pl

from . import config
from .sources import SOURCES

B = 1e9  # report in USD billions


def _n_anchors(comp: str, target_key: str) -> int:
    """Distinct independent hard/analyst sources informing this component for this target."""
    names = {s["name"] for s in SOURCES
             if target_key in s["targets"] and comp in s["component"]
             and s["confidence"] in config.ANCHOR_CONF}
    return len(names)


def _confidence(n_anchors: int, cv: float) -> tuple[str, float]:
    """Earned confidence: needs independent anchors AND family agreement (low dispersion)."""
    if n_anchors >= config.CONF_HIGH["min_anchors"] and cv < config.CONF_HIGH["max_cv"]:
        label = "high"
    elif n_anchors >= config.CONF_MED["min_anchors"] and cv < config.CONF_MED["max_cv"]:
        label = "medium"
    else:
        label = "low"
    agree = max(0.0, 1 - cv / config.CV_REF)
    score = round(min(1.0, n_anchors / 3) * agree, 2)
    return label, score


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


def _base_levels(t: dict, epoch: pl.DataFrame) -> dict:
    """Prior-quarter level (USD) per component for this target."""
    kind, ref = t["base"][0], t["base"][1]
    if kind == "epoch":
        row = epoch.filter(pl.col("Quarter") == ref)
        return {c: row[c][0] for c in config.COMPONENTS}
    if kind == "chain":  # read prior target's reconciled_base ($B) -> USD
        prior = pl.read_csv(config.PROC_DIR / ref).filter(pl.col("component") != "TOTAL")
        return {r["component"]: r["reconciled_base"] * B for r in prior.iter_rows(named=True)}
    raise ValueError(f"unknown base kind {kind!r}")


def _estimates(comp: str, L: float, median_qoq: float, scenario: str, t: dict) -> dict:
    """All estimates for one component as full-quarter levels (USD)."""
    est = {
        "trend": L * (1 + median_qoq),
        "supply": L * (1 + t["supply_qoq"][comp][scenario]),
        "demand": L * (1 + t["demand_qoq"][comp][scenario]),
        "macro": L * (1 + median_qoq) * t["macro_scaler"][scenario],
    }
    if comp == "Memory":  # explicit price x volume decomposition
        est["price"] = L * (1 + t["volume_qoq"][scenario]) * (1 + t["price_qoq"][scenario])
    else:
        est["price"] = est["trend"]  # no memory-style price index for these
    if t.get("analyst_qoq"):
        est["analyst"] = L * (1 + t["analyst_qoq"][comp][scenario])
    est["reconciled"] = sum(t["weights"][k] * est[k] for k in t["weights"])
    return est


def run(target_key: str) -> dict:
    config.PROC_DIR.mkdir(parents=True, exist_ok=True)
    t = config.TARGETS[target_key]
    epoch = _quarterly_totals()
    epoch.drop("_k").with_columns([(pl.col(c) / B) for c in config.COMPONENTS]).write_csv(
        config.PROC_DIR / "nowcast_history.csv")  # Epoch 4-designer totals ($B)
    base = _base_levels(t, epoch)
    complete = epoch.filter(pl.col("_k") < _qkey(target_key))  # only quarters before the target

    # Chained forecasts compound the prior quarter's uncertainty -> widen the band.
    rel_prior = 0.0
    if t["base"][0] == "chain":
        pr = pl.read_csv(config.PROC_DIR / t["base"][1]).filter(pl.col("component") == "TOTAL").row(0, named=True)
        rel_prior = ((pr["high"] - pr["low"]) / 2) / pr["reconciled_base"]

    rows, detail = [], []
    for comp in config.COMPONENTS:
        series = complete[comp].to_list()
        qoq = [series[i] / series[i - 1] - 1 for i in range(1, len(series))]
        median_qoq = sorted(qoq)[len(qoq) // 2]
        L = base[comp]
        partial = epoch.filter(pl.col("Quarter") == target_key)[comp]
        partial = (partial[0] if partial.len() else None)

        b = _estimates(comp, L, median_qoq, "base", t)
        lo = _estimates(comp, L, median_qoq, "low", t)
        hi = _estimates(comp, L, median_qoq, "high", t)
        rb = b["reconciled"]

        # Data-driven uncertainty: dispersion across all family estimates and scenarios,
        # plus a floor that shrinks with the number of independent anchors.
        fams = [k for k in b if k != "reconciled"]
        spread = [e[f] for e in (lo, b, hi) for f in fams]
        cv = pstdev(spread) / mean(spread) if mean(spread) else 0.0
        n_anchors = _n_anchors(comp, target_key)
        hw_rel = (cv ** 2 + (config.BASE_HW / (n_anchors + 1) ** 0.5) ** 2) ** 0.5
        if rel_prior:  # chained forecast compounds the prior quarter's uncertainty
            hw_rel = (hw_rel ** 2 + rel_prior ** 2) ** 0.5
        confidence, score = _confidence(n_anchors, cv)
        rows.append({
            "component": comp,
            "partial_actual": (partial / B if partial is not None else None),
            "supply_side": b["supply"] / B,
            "demand_side": b["demand"] / B,
            "price_adjusted": b["price"] / B,
            "macro_calibrated": b["macro"] / B,
            "analyst_side": (b["analyst"] / B if "analyst" in b else None),
            "trend_only": b["trend"] / B,
            "reconciled_base": rb / B,
            "low": rb * (1 - hw_rel) / B,
            "high": rb * (1 + hw_rel) / B,
            "confidence": confidence,
            "confidence_score": score,
            "n_anchors": n_anchors,
            "dispersion_cv": round(cv, 3),
        })
        for est in [k for k in ["trend", "supply", "demand", "price", "macro", "analyst", "reconciled"] if k in b]:
            detail.append({"component": comp, "estimate": est, "value_b": b[est] / B})

    out = pl.DataFrame(rows)
    total = {"component": "TOTAL", "confidence": "-"}
    for col in ["partial_actual", "supply_side", "demand_side", "price_adjusted",
                "macro_calibrated", "analyst_side", "trend_only", "reconciled_base", "low", "high"]:
        total[col] = out[col].sum()
    out = pl.concat([out, pl.DataFrame([total])], how="diagonal_relaxed")

    stem = t["output"].removesuffix(".csv")
    out.write_csv(config.PROC_DIR / t["output"])
    pl.DataFrame(detail).write_csv(config.PROC_DIR / f"{stem}_estimates_detail.csv")

    r = out.filter(pl.col("component") == "TOTAL").row(0, named=True)
    print(f"  {target_key} ({t['kind']}) reconciled base TOTAL: ${r['reconciled_base']:.1f}B "
          f"(low ${r['low']:.1f}B - high ${r['high']:.1f}B); trend-only ${r['trend_only']:.1f}B")
    return {"total": r, "table": out}
