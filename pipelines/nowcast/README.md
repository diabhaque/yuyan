# Q1 2026 AI-chip component-spend nowcast

Nowcasts full-quarter **Q1 2026** component spend (Memory / Logic / Packaging / Auxiliary)
for AI chips designed by **NVIDIA, AMD, Google, Amazon**, by triangulating real external
signals against the Epoch trend baseline.

**Why:** Epoch's `ai_chip_components` data lags — its Q1 2026 quarter is missing NVIDIA
(historically 64–77% of these designers' spend), so the raw partial is unusable as a total.
Q1 2026 (Jan–Mar) is in the past, so real actuals exist to fill the gap.

## Run
```
uv run -m pipelines.nowcast all      # fetch -> process -> model
# or: fetch | process | model
```
Outputs: `data/raw/nowcast/` (evidence + FRED CSV), `data/processed/nowcast/`
(`company.csv`, `price.csv`, `macro.csv`, `nowcast_q1_2026.csv`, `nowcast_history.csv`,
`nowcast_estimates_detail.csv`), `datasources/nowcast_sources.csv` (committed registry).
Plots: `notebooks/chip_spend_nowcast_viz.ipynb`.

## Headline (base scenario)
Reconciled **Q1 2026 total ≈ $24.0B** (low $22.0B – high $27.1B) vs **trend-only $23.0B**.
By component ($B): Memory 16.5 (15–19), Logic 2.7, Packaging 3.1, Auxiliary 1.8.

## Source → component mapping
| Family | Source | Informs | Strength |
|---|---|---|---|
| A suppliers (hard) | SK hynix, Micron, Samsung | Memory | high |
| A suppliers (hard) | TSMC (monthly + Q1) | Logic, Packaging | high/medium |
| A buyers (directional) | NVIDIA (DC rev), hyperscaler capex | Logic, Auxiliary | qualitative |
| B price | TrendForce DRAM/NAND/HBM contract Δ | Memory (price) | hard-price |
| C macro | Korea exports, FRED `IPG3344S` | all (quarter pace) | macro |

Every figure with its URL + as-of date is in `sources.py` and `datasources/nowcast_sources.csv`.
All weights/assumptions are editable named parameters in `config.py`.

## Model (per component)
Builds five full-quarter estimates from real scalars applied to the Q4 2025 level:
- **trend** — Epoch median QoQ growth (data only).
- **supply** — supplier-revenue-implied QoQ (SK hynix +60% QoQ; TSMC pace).
- **demand** — buyer-side (NVIDIA DC ~2× YoY, capex), directional.
- **price_adjusted** — Memory only: `level × (1+volume) × (1+price)` using TrendForce Q1'26
  contract price (~+95% DRAM; HBM more LTA-priced, so a conservative +50% base is used).
- **macro** — trend × Korea/FRED pace scalar.

**Reconciliation** (not addition): suppliers and buyers are two views of the *same* spend.
Weighted blend — hard supplier > price > trend > macro > qualitative buyer
(`config.WEIGHTS`). low/high re-run the blend under low/high parameter sets.

## Price decomposition (Memory)
Memory `$ = price × volume`. Q1 2026 saw a large memory **price** jump, so the `price_adjusted`
estimate separates the contract-price uplift from bit-volume growth — otherwise a price-driven
move would be misread as volume (or vice-versa).

## Double-counting controls
HBM **sold** by Micron/SK hynix/Samsung is the same dollars as HBM **bought** by NVIDIA et al.
Supplier and buyer signals are therefore **reconciled, never summed**; supplier revenue is the
anchor and buyer guidance only a directional scaler (low weight).

## Per-component confidence
Memory **high** (hard supplier + price data); Logic **medium** (TSMC anchor, NVIDIA allocation
uncertain); Packaging/Auxiliary **low** (weak/qualitative supplier mapping → trend-anchored).

## Limitations
- NVIDIA's per-component split is the dominant uncertainty; buyer fiscal calendars are
  offset ~1 month from calendar Q1 (NVIDIA, Micron).
- HBM exact $ to these four buyers is not cleanly disclosed; growth rates/shares used instead.
- Not obtained (→ trend fallback, noted): Taiwan MOEA, SEMI billings, OSAT revenue, exact
  NVIDIA DC / Samsung DS / Micron USD figures.
- **This is a nowcast, not a guarantee.** All inputs are real and traceable (URL + as-of);
  nothing is invented or silently interpolated.
