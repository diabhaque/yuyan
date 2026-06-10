"""External evidence registry for the Q1 2026 nowcast.

Every figure below was read from the cited official/primary release (URL + as_of).
Values are transcribed, not invented; where only a growth rate or qualitative tone was
disclosed, that is what is recorded. Family: A=company, B=price, C=macro/trade.
"""

# family, name, component(s) informed, metric, value, period, url, as_of, confidence, note
SOURCES = [
    # --- (A) Suppliers — hard revenue ---
    dict(family="A", name="TSMC", component=["Logic", "Packaging"],
         metric="Q1 2026 revenue", value="US$35.90B (+40.6% YoY)", period="Q1 2026",
         url="https://pr.tsmc.com/english/news/3294", as_of="2026-04-10",
         confidence="hard",
         note="Monthly Jan-Mar; Mar 2026 NT$415.19B (+45.2% YoY); 7nm-and-below = 74% of wafer rev. Logic+CoWoS pace anchor."),
    dict(family="A", name="SK hynix", component=["Memory"],
         metric="Q1 2026 revenue", value="KRW 52.58T (+198% YoY, +60% QoQ)", period="Q1 2026",
         url="https://news.skhynix.com/q1-2026-business-results/", as_of="2026-04-23",
         confidence="hard",
         note="Record; HBM ~57% share; HBM demand exceeds planned 3-yr capacity. Memory supply anchor."),
    dict(family="A", name="Micron", component=["Memory"],
         metric="FQ2 2026 revenue", value="~+196% YoY (~tripled)", period="FQ2'26 (ended ~Feb 2026, offset)",
         url="https://investors.micron.com/news-releases/news-release-details/micron-technology-inc-reports-results-second-quarter-fiscal-2026",
         as_of="2026-03-18", confidence="hard",
         note="Offset fiscal calendar; record revenue; 2026 HBM sold out. Memory supply corroboration."),
    dict(family="A", name="Samsung", component=["Memory"],
         metric="Q1 2026 semiconductor profit", value="memory op profit ~50x YoY", period="Q1 2026",
         url="https://news.samsung.com/global/samsung-electronics-announces-first-quarter-2026-results",
         as_of="2026-04-30", confidence="qualitative",
         note="Group op profit > FY25 full-year total; memory-led; warns 2027 shortage. Directional only."),
    # --- (A) Buyers/designers — directional ---
    dict(family="A", name="NVIDIA", component=["Logic", "Auxiliary"],
         metric="Q1 FY2027 revenue", value="US$81.6B total (+85% YoY); Data Center ~90% (~$73B), ~2x YoY",
         period="FQ1'27 (~Feb-Apr 2026, offset)",
         url="https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-first-quarter-fiscal-2027",
         as_of="2026-05-20", confidence="qualitative",
         note="Buyer demand scaler; fiscal qtr offset ~1 month vs calendar Q1. Two views of same spend as suppliers -> reconcile."),
    # --- (B) Memory price indices ---
    dict(family="B", name="TrendForce", component=["Memory"],
         metric="Q1 2026 DRAM contract price QoQ", value="~+95% DRAM; NAND up; HBM tight (LTA)",
         period="Q1 2026",
         url="https://www.trendforce.com/presscenter/news/20260202-12911.html", as_of="2026-02-02",
         confidence="hard-price",
         note="Free press release. Drives Memory price x volume decomposition; HBM more LTA-priced so contract uplift < DRAM spot."),
    # --- (C) Macro / trade ---
    dict(family="C", name="Korea MOTIE/customs", component=["all"],
         metric="Mar 2026 semiconductor exports YoY", value="~+200% (through 20th); record monthly exports",
         period="Mar 2026",
         url="https://en.sedaily.com/finance/2026/04/01/semiconductor-power-defies-war-monthly-exports-head-toward",
         as_of="2026-04-01", confidence="macro",
         note="Record Q1 exports, chip-led. Quarter-pace calibration (at/above trend)."),
    dict(family="C", name="FRED IPG3344S", component=["all"],
         metric="US semiconductor industrial production index", value="<fetched live>", period="monthly",
         url="https://fred.stlouisfed.org/series/IPG3344S", as_of="fetched at runtime",
         confidence="macro", note="Downloaded as CSV by loaders; recent YoY used as pace cross-check."),
]

# Sources NOT obtained (mapped to trend fallback; see README limitations):
NOT_OBTAINED = [
    "Taiwan MOEA export orders (corroborated by TSMC + Korea)",
    "SEMI billings / book-to-bill",
    "OSAT (ASE, Amkor) packaging revenue",
    "Exact NVIDIA Data Center USD, exact Samsung DS USD, exact Micron USD (used growth rates / shares instead)",
]

FRED_SERIES = "IPG3344S"
FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=IPG3344S"
