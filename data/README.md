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

### Blob-card variants
- **Multi-file dataset** (a directory of CSVs): set `blob_path` to the directory, `format` to
  `"csv (N files)"`, list `files: [{name, rows, columns}]` (or `files_sample` + `file_count` when
  there are too many to enumerate), and set top-level `columns` to the primary file's headers or
  `null` when they vary per file (note it in `how_to_read`). Example: `rd_epoch-benchmarks_b5d6`.
- **Pointer card** (a known source whose data hasn't been retrieved): set `blob_path: null` and put
  the access info in `body` (`endpoint`, `provider`, `coverage`, `access`, `update_frequency`,
  `signal`, `model_role`, `how_to_read`). Columns/row_count are omitted. Used for the free
  supply/demand source catalog (`rd_wsts-billings_7a10`, …) and github repos with no CSV export.
- **Shared blob, one record per entity**: many records may point at the *same* blob, each selecting
  a slice via a `how_to_read` filter — e.g. one `pd_price-<ticker>_*` record per stock over the
  single `data/blobs/prices.csv` (filter `primary_id == '<ticker>'`).

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

## Soft locks — `data/records/_locks.json`
A single JSON object (starts `{}`) so two agents don't improve the same record at once. Keyed by
record id:
```json
{ "fc_sox-index_a1b2": { "agent": "builder", "since": "2026-06-13T10:00:00Z",
                         "ttl_minutes": 30, "note": "sourcing PHLX value" } }
```
- **Acquire** — read the file; if your id is present and not stale, back off (pick another target);
  else add your entry and write back.
- **Release** — remove your entry on completion (success *or* abort).
- **Stale reclaim** — an entry past `since + ttl_minutes` may be overwritten.
- **Contention** — the file is shared, so the orchestrator hands each parallel agent a **disjoint**
  set of target ids; concurrent writers never touch the same lock. (Don't overengineer at this scale.)

Files named `_*` under `data/records/` (`_locks.json`, `_cultivate_log.jsonl`) are orchestration
bookkeeping, **not records** — scans skip them.

## Agents & the cultivation loop
The store is cultivated by four subagents (`.claude/agents/`), each also runnable standalone via a
slash command (`.claude/commands/`), and orchestrated by `/cultivate`:
- **thinker** (`/think "<goal>"`) — *propose.* Decomposes a goal into a **metric graph**, scans for
  what exists, and writes **proposal records** for what's missing.
- **builder** (`/build [id]`) — *improve.* Raises a record's confidence by sourcing or computing its
  value; may build pipelines/blobs and expand the graph.
- **verifier** (`/verify [scope]`) — *cross-check.* Source reliability, figure↔source factuality,
  and cross-record logical consistency (`total == Σ parts`). Flags, never silently rewrites.
- **organizer** (`/organize [scope]`) — *tidy.* Envelope repair, edge health, dedup/consolidation,
  pruning, tag hygiene.

`/cultivate "<goal>" [--max-cycles N]` runs the **dynamic loop**: **sense** the datastore (ad-hoc
scan — counts, confidence histogram, priority queue, orphans, invariant violations, active locks,
goal coverage) → **decide** which agents to dispatch from that snapshot → **act** (parallel where
lock-disjoint) → **integrate** (log to `_cultivate_log.jsonl`) → **loop** until converged or capped.

### Conventions the loop relies on
- **Proposal record** — a thinker's stub: `confidence: 0`, a **placeholder value with units**, and
  `inputs`/`adjacency` edges describing where its real value will come from. (`confidence 0` is the
  only legitimate use of zero — see the envelope rules.) A builder later fills it and raises confidence.
- **Metric graph** — just the `inputs`/`adjacency` edges. Identities are **bidirectional**
  (`total = a + b` ⇒ `a = total − b`); information flows from higher- to lower-confidence nodes.
- **Builder priority** — work the **lowest confidence first, ties broken by highest degree**
  (`|inputs| + |adjacency|`): the weakest, most-depended-on metrics first.
