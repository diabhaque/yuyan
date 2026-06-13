---
description: Run the Organizer agent standalone — validate envelopes, fix edges, consolidate duplicates, prune stale records, improve tags.
argument-hint: "[scope: tag/topic or 'all']"
---

Dispatch a single **organizer** subagent (via the Agent tool, `subagent_type: organizer`) over this
scope:

> $ARGUMENTS

If empty, default to `all`. The organizer should resolve the scope to concrete ids by scanning
`data/records/`, lock records before editing them, and do its integrity passes (envelope
validation/repair, edge health, consolidation of duplicates/same-fact records, deletion of
stale/useless records, tag improvement) per `data/README.md`.

When it returns, summarize the change log: repairs, edge fixes, consolidations, deletions, tag changes.
