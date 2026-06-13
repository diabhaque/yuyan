---
description: Run the Builder agent standalone — raise the confidence of one record by sourcing or computing its real value.
argument-hint: "[record-id]"
---

Dispatch a single **builder** subagent (via the Agent tool, `subagent_type: builder`) targeting:

> $ARGUMENTS

If a record id is given, build that record. If the argument is empty, the builder should scan
`data/records/` and pick the highest-priority target itself (**lowest confidence first, ties broken
by highest degree** `|inputs| + |adjacency|`).

The builder should lock the target in `data/records/_locks.json`, find the value from a reliable
free source or compute it from upstream records/blobs (per `data/README.md` and
[[nowcast-methodology]]), write the value + units back, raise confidence by role, maintain the
`inputs ↔ adjacency` invariant, and release the lock.

When it returns, summarize what changed and the new confidence.
