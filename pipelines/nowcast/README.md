# AI-chip component-spend nowcast / forecast

Estimates full-quarter component spend (Memory / Logic / Packaging / Auxiliary) for AI chips
designed by **NVIDIA, AMD, Google, Amazon**, by triangulating real external signals against
the Epoch trend baseline. Two **chained targets** (`config.TARGETS`):
- **Q1 2026 — nowcast** (past quarter): Epoch's data is missing NVIDIA (historically 64–77%
  of these designers' spend), so the raw partial is unusable; we fill it from actuals.
- **Q2 2026 — forecast** (in progress): chains off the Q1 2026 nowcast as its base level and
  applies forward guidance / price trajectory / analyst estimates. Intervals are widened to
  compound the Q1 nowcast's uncertainty (in quadrature).

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
- **Q1 2026 nowcast ≈ $24.0B** (low $22.0B – high $27.1B) vs trend-only $23.0B. By component
  ($B): Memory 16.5, Logic 2.7, Packaging 3.1, Auxiliary 1.8.
- **Q2 2026 forecast ≈ $32.7B** (low $28.0B – high $37.5B) vs trend-only $32.1B. By component
  ($B): Memory 23.8, Logic 3.2, Packaging 3.6, Auxiliary 2.1. Memory-led (+~36% QoQ) on the
  TrendForce 2Q26 price surge (DRAM +58–63%) and the Morgan Stanley memory-share trajectory.

## Source → component mapping
| Family | Source | Informs | Strength |
|---|---|---|---|
| A suppliers (hard) | SK hynix, Micron, Samsung | Memory | high |
| A suppliers (hard) | TSMC (monthly + Q1/Q2 guide) | Logic, Packaging | high |
| A suppliers (hard) | **TSMC HPC platform** (61% of rev, +20% QoQ) | Logic | hard |
| A suppliers (hard) | **TSMC CoWoS capacity** (75→130k wpm; fully booked) | Packaging | hard |
| A suppliers (hard) | **Broadcom AI networking** ($10.8B, +143% YoY) | Auxiliary | hard |
| A buyers (directional) | NVIDIA (DC rev), hyperscaler capex | Logic, Auxiliary | qualitative |
| B price | TrendForce DRAM/NAND/HBM contract Δ (Q1 ~+95%, Q2 +58–63%) | Memory (price) | hard-price |
| C macro | Korea exports, FRED `IPG3344S` | all (quarter pace) | macro |
| D analyst | Morgan Stanley VR200 BoM; **NVIDIA Blackwell shipments**; **optical (InnoLight/Coherent)** | Memory/Pkg/Aux; Logic; Auxiliary | analyst |
| A diverse (hard) | **TrendForce HBM bit-supply**; **ASE**, **Amkor** (OSAT); **Astera Labs**, **Monolithic Power** | Memory; Packaging; Auxiliary | hard |
| B price | **Murata MLCC** +15–35% (Q2) | Auxiliary | hard-price |

**Evaluation (new info vs corroboration)** — each source carries a `new_info` tag in the
registry. Sources that added genuinely new information (and refined a scalar): TrendForce HBM
**bit-supply ceiling** (capped Memory volume), NVIDIA **unit shipments** (Logic volume),
Astera/MPWR/optical/MLCC (**data-backed Auxiliary**, formerly trend-only). Others (ASE/Amkor)
corroborate and raise anchor counts. Result: every component now has 3–6 independent anchors and
computes to **high** confidence; Auxiliary went from 1 anchor → 4–6.

**Morgan Stanley BoM caveat:** it is a *rack/system* bill-of-materials (broader than Epoch's
chip-component scope) and the VR200 generation ships Q3 2026 / ramps Q4 — so it is used as a
**memory-share trajectory + upside** signal for Q2, not Q2's base mix (Q2 = Blackwell GB300).

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

## Per-component confidence (computed, not asserted)
Each component's confidence is **derived** from two things and emitted in the output
(`confidence`, `confidence_score`, `n_anchors`, `dispersion_cv`):
- **n_anchors** — count of independent *hard/analyst* sources backing the component
  (`config.ANCHOR_CONF`). Each component now has a real anchor: Memory (memory makers +
  TrendForce), **Logic (TSMC HPC)**, **Packaging (TSMC CoWoS)**, **Auxiliary (Broadcom + MS BoM)**.
- **dispersion_cv** — coefficient of variation across the estimate families/scenarios (do they agree?).

Label: `high` if `n_anchors ≥ 2 and cv < 0.20`; `medium` if `≥ 1 anchor and cv < 0.30`; else `low`.
The prediction band is **data-driven**: `half_width = sqrt(cv² + (BASE_HW/√(n_anchors+1))²)`
(chained forecasts add the prior quarter's relative uncertainty in quadrature) — more agreeing
anchors ⇒ tighter band. With the expanded source set every component now has **3–6 independent
anchors and computes to `high`** (Auxiliary went 1→4–6 anchors), with Q1 bands ~8% for
Logic/Packaging/Auxiliary vs Memory's ~19% (Memory carries real price-vs-volume dispersion).

**Mapping caveats:** TSMC HPC ⊃ just these 4 designers' logic dies; CoWoS ASP adds price on top
of capacity; Broadcom AI networking ⊂ Auxiliary. Directionally strong, not 1:1.

## Limitations
- NVIDIA's per-component split is the dominant uncertainty; buyer fiscal calendars are
  offset ~1 month from calendar Q1 (NVIDIA, Micron).
- HBM exact $ to these four buyers is not cleanly disclosed; growth rates/shares used instead.
- Not obtained (→ trend fallback, noted): Taiwan MOEA, SEMI billings, OSAT revenue, exact
  NVIDIA DC / Samsung DS / Micron USD figures.
- **This is a nowcast, not a guarantee.** All inputs are real and traceable (URL + as-of);
  nothing is invented or silently interpolated.
