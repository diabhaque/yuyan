# `data/` — the record datastore (for agents, by agents)

A flat tree of small JSON **records** plus large **blobs**. There is **no access library** — agents
(notebooks, future agents) read, write, and scan these files directly with general tools
(`pathlib.rglob` + `json`, polars for blobs). The rules below are a *layout contract*, not an API.
Records are authored by an agent reading a source and writing down what matters — there is no
standard article→record pipeline.

```
data/
├── records/
│   ├── facts/            # hard quantitative ground truth (SEC, official macro)   — date-bucketed
│   ├── forecasts/        # model/agent predictions                                — date-bucketed
│   ├── computations/     # intermediate derivations kept as records               — date-bucketed
│   ├── news/             # figures transcribed from articles / press / analysts   — date-bucketed
│   ├── raw_data/         # cards describing as-downloaded blobs                    — flat
│   └── processed_data/   # cards describing cleaned / derived blobs                — flat
└── blobs/                # large files: csv, parquet, transcripts, …
```

`data_old/` (gitignored) holds the pre-refactor `data/raw` + `data/processed`; `datasources_old/`
holds the old source-registry CSVs. Both are superseded by records and will be removed later.

## Record id & file path
- **One JSON file per record; filename = id.** Id = `{prefix}_{slug}_{4hex}` where `slug` is a short
  kebab-case description and the suffix is 4 random hex chars. Prefix by type:
  `facts→fct`, `forecasts→fc`, `computations→cmp`, `news→nws`, `raw_data→rd`, `processed_data→pd`.
  e.g. `rd_epoch-chip-components_8b0f.json`, `fc_chip-component-spend-q1-2026_3c7d.json`.
- **High-churn types** (`facts`, `forecasts`, `computations`, `news`) live in **date buckets** by
  `ts_recorded`: `records/<type>/<YYYY>/<MM>/<id>.json`. **Blob cards** (`raw_data`,
  `processed_data`) stay **flat**: `records/<type>/<id>.json`.

## Record envelope (mandatory — exactly these top-level fields)
```json
{
  "id": "string",
  "type": "facts|forecasts|computations|news|raw_data|processed_data",
  "description": "one-line human/LLM-readable summary",
  "tags": ["free-form", "grouping", "strings"],
  "ts_recorded": "ISO-8601 timestamp this record was written",
  "ts_applies": "period the content applies to (date, quarter like 2026-Q3, range, or null)",
  "confidence": 0.0,
  "source": "URL | agent:<name> | notebook:<path> | pipeline:<path>",
  "body": {},
  "adjacency": ["ids of records that DEPEND ON this one (downstream)"],
  "methodology": {
    "summary": "how the numbers in body were produced",
    "inputs": ["ids of records this was derived FROM (upstream)"],
    "code": "path to notebook/pipeline, or null"
  }
}
```

### Rules
- **`confidence` ∈ [0,1].** `0` only for proposed-but-unverified values (a verified claim is never
  exactly 0). Migrated source data defaults to `0.8` unless there's a reason otherwise — document the
  choice in `methodology.summary`. (This datapoint sets confidence by role: hard/hard-price `0.8`,
  analyst `0.6`, qualitative `0.4`.)
- **`adjacency` and `methodology.inputs` are inverses.** `inputs` is the source of truth; `adjacency`
  is derived. **Invariant:** whenever you write record `X` with `inputs:[A,B]`, also append `X.id` to
  `A.adjacency` and `B.adjacency` (dedup). Discover records by scanning + filtering on `tags`/`type`.
- **Numeric `body` values carry units** (e.g. a sibling `units` map, or a unit suffix in the key).
- **Blob cards** (`raw_data`/`processed_data`): `body` must contain at least `blob_path`, `format`,
  `columns` (if tabular), `row_count`, and a `how_to_read` note.

## Worked example: chip component spend
Lineage built by `notebooks/chip_component_spend_v2.ipynb`:
```
rd_epoch-chip-components  (raw_data: Epoch CSV blob)
  └─> pd_chip-spend-history (processed_data: quarterly history blob)
        ├─> pd_chip-spend-q1-estimates ─> fc_chip-component-spend-q1-2026 (nowcast)
        └─> pd_chip-spend-q2-estimates ─> fc_chip-component-spend-q2-2026 (forecast)
20 news + 3 facts datasource records ──> the two estimate cards
fc_…-q1-2026 ──> fc_…-q2-2026   (Q2 chains off the Q1 nowcast)
```
The notebook reads every input by scanning `data/records/` (tag `chip-component-spend`) and writes
its forecast back as the `fc_…` records above.
