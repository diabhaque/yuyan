"""All editable parameters for the Q1 2026 nowcast. Tune here, not in the model."""

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
TARGET_QUARTER = "Q1 2026"
LAST_COMPLETE = "Q4 2025"

# Approx FX for display of supplier revenue (Q1 2026 avg). Model uses growth rates, not FX.
FX_TO_USD = {"USD": 1.0, "KRW": 1 / 1380.0, "TWD": 1 / 32.0}

# --- Growth scalars (QoQ vs Q4 2025), per component, by scenario. ---
# Each is sourced from the real signals in sources.py (see notes there).
PRICE_QOQ = {"low": 0.30, "base": 0.50, "high": 0.80}      # Memory contract price, TrendForce Q1'26
VOLUME_QOQ = {"low": 0.05, "base": 0.12, "high": 0.20}     # HBM bit-volume ramp QoQ
SUPPLY_QOQ = {  # supplier-revenue-implied QoQ growth per component
    "Memory": {"low": 0.35, "base": 0.55, "high": 0.85},   # SK hynix +60% QoQ, Micron +196% YoY
    "Logic": {"low": 0.06, "base": 0.12, "high": 0.18},    # TSMC Q1'26 +40.6% YoY / monthly pace
    "Packaging": {"low": 0.04, "base": 0.10, "high": 0.18},# TSMC CoWoS expansion (weaker mapping)
    "Auxiliary": {"low": 0.03, "base": 0.08, "high": 0.15},# weakest mapping
}
DEMAND_QOQ = {  # buyer-side (NVIDIA DC ~2x YoY, hyperscaler capex) directional
    "Memory": {"low": 0.05, "base": 0.12, "high": 0.20},
    "Logic": {"low": 0.08, "base": 0.15, "high": 0.25},
    "Packaging": {"low": 0.05, "base": 0.12, "high": 0.20},
    "Auxiliary": {"low": 0.04, "base": 0.10, "high": 0.18},
}
MACRO_SCALER = {"low": 0.95, "base": 1.00, "high": 1.08}   # Korea +~200% YoY semis, TSMC +40% YoY

# --- Reconciliation weights (must reflect: hard supplier > price > trend > macro > qualitative buyer). ---
WEIGHTS = {"supply": 0.30, "price": 0.30, "trend": 0.20, "macro": 0.12, "demand": 0.08}

# Per-component confidence (drives interpretation, not math).
CONFIDENCE = {"Memory": "high", "Logic": "medium", "Packaging": "low", "Auxiliary": "low"}
