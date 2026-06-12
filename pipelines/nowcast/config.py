"""All editable parameters for the AI-chip component-spend nowcast/forecast.
Tune here, not in the model. Targets are quarter-parameterized and can chain
(Q2 2026 forecast builds on the Q1 2026 nowcast output)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BASE_CSV = ROOT / "data" / "processed" / "epoch_ai" / "ai_chip_components__quarterly_by_chip.csv"
RAW_DIR = ROOT / "data" / "raw" / "nowcast"
PROC_DIR = ROOT / "data" / "processed" / "nowcast"

TARGET_DESIGNERS = ["NVIDIA", "AMD", "Google", "Amazon"]  # exclude the "Other" catch-all
COMPONENTS = ["Memory", "Logic", "Packaging", "Auxiliary"]
COST_COL = {  # component -> Epoch cost column (already cost x volume, USD)
    "Memory": "HBM cost (USD) (median)",
    "Logic": "Logic cost (USD) (median)",
    "Packaging": "CoWoS cost (USD) (median)",
    "Auxiliary": "Auxiliary cost (USD) (median)",
}
# Approx FX for display of supplier revenue. Model uses growth rates, not FX.
FX_TO_USD = {"USD": 1.0, "KRW": 1 / 1380.0, "TWD": 1 / 32.0}

# --- Data-driven confidence + prediction-band params ---
# Confidence is computed per component from (a) how many independent hard anchors back it and
# (b) how well the estimate families agree (dispersion). It is earned, not asserted.
ANCHOR_CONF = {"hard", "hard-price", "analyst"}  # source `confidence` values that count as anchors
BASE_HW = 0.12      # base relative half-width for a single anchor; shrinks ~1/sqrt(n_anchors+1)
CV_REF = 0.35       # dispersion that maps to a zero agreement-score
CONF_HIGH = {"min_anchors": 2, "max_cv": 0.20}   # else medium if >=1 anchor and cv<0.30, else low
CONF_MED = {"min_anchors": 1, "max_cv": 0.30}

# --- Targets. Each: base (where the prior-quarter level comes from), QoQ scalars per
#     family/scenario, and reconciliation weights. ---
TARGETS = {
    "Q1 2026": {  # nowcast: Epoch is missing NVIDIA, so fill the quarter
        "kind": "nowcast",
        "base": ("epoch", "Q4 2025"),       # level from Epoch actual
        "output": "nowcast_q1_2026.csv",
        "price_qoq": {"low": 0.30, "base": 0.50, "high": 0.80},   # TrendForce Q1'26 DRAM ~+95%
        "volume_qoq": {"low": 0.04, "base": 0.10, "high": 0.16},  # HBM bit-supply capacity-constrained (TrendForce)  # HBM bit-volume ramp
        "supply_qoq": {                                            # supplier-revenue-implied QoQ
            "Memory": {"low": 0.35, "base": 0.55, "high": 0.85},  # SK hynix +60% QoQ, Micron +196% YoY
            "Logic": {"low": 0.15, "base": 0.20, "high": 0.25},   # TSMC HPC +20% QoQ Q1'26 (anchor)
            "Packaging": {"low": 0.10, "base": 0.14, "high": 0.18},# CoWoS capacity +ASP (~+14%/qtr)
            "Auxiliary": {"low": 0.08, "base": 0.13, "high": 0.18},# Broadcom AI networking (anchor)
        },
        "demand_qoq": {  # buyer-side directional (NVIDIA DC ~2x YoY)
            "Memory": {"low": 0.05, "base": 0.12, "high": 0.20},
            "Logic": {"low": 0.08, "base": 0.15, "high": 0.25},
            "Packaging": {"low": 0.05, "base": 0.12, "high": 0.20},
            "Auxiliary": {"low": 0.04, "base": 0.10, "high": 0.18},
        },
        "macro_scaler": {"low": 0.95, "base": 1.00, "high": 1.08},
        "analyst_qoq": None,
        "weights": {"supply": 0.30, "price": 0.30, "trend": 0.20, "macro": 0.12, "demand": 0.08},
    },
    "Q2 2026": {  # forecast (Apr-Jun, in progress); chains off the Q1 2026 nowcast
        "kind": "forecast",
        "base": ("chain", "nowcast_q1_2026.csv"),  # prior-quarter level = Q1 2026 reconciled_base
        "output": "forecast_q2_2026.csv",
        "price_qoq": {"low": 0.30, "base": 0.45, "high": 0.60},   # TrendForce 2Q26 DRAM +58-63%; HBM LTA rises less
        "volume_qoq": {"low": 0.04, "base": 0.10, "high": 0.16},  # HBM bit-supply capacity-constrained (TrendForce)
        "supply_qoq": {
            "Memory": {"low": 0.30, "base": 0.45, "high": 0.65},  # memory-maker Q2 guidance / LTAs
            "Logic": {"low": 0.08, "base": 0.11, "high": 0.14},   # TSMC Q2 guide ~+10% QoQ; HPC-led (anchor)
            "Packaging": {"low": 0.09, "base": 0.12, "high": 0.16},# CoWoS capacity ramp continues (anchor)
            "Auxiliary": {"low": 0.09, "base": 0.13, "high": 0.17},# Astera +14%/MPWR +12.6% QoQ + MLCC price (anchors)
        },
        "demand_qoq": {
            "Memory": {"low": 0.05, "base": 0.12, "high": 0.20},
            "Logic": {"low": 0.06, "base": 0.12, "high": 0.20},
            "Packaging": {"low": 0.05, "base": 0.10, "high": 0.18},
            "Auxiliary": {"low": 0.04, "base": 0.09, "high": 0.16},
        },
        "macro_scaler": {"low": 0.97, "base": 1.02, "high": 1.10},
        "analyst_qoq": {  # Morgan Stanley VR200 BoM: memory share rising; pkg/aux costs up (PCB/MLCC/ABF)
            "Memory": {"low": 0.25, "base": 0.40, "high": 0.60},
            "Logic": {"low": 0.05, "base": 0.10, "high": 0.16},
            "Packaging": {"low": 0.06, "base": 0.12, "high": 0.20},
            "Auxiliary": {"low": 0.05, "base": 0.10, "high": 0.18},
        },
        # supplier > price > trend > analyst > macro > qualitative buyer
        "weights": {"supply": 0.26, "price": 0.26, "trend": 0.18, "analyst": 0.12,
                    "macro": 0.10, "demand": 0.08},
    },
}
RUN_ORDER = ["Q1 2026", "Q2 2026"]
