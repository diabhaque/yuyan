---
description: Run the Verifier agent standalone — audit records for source reliability, factuality, and logical consistency.
argument-hint: "[scope: tag/topic, record-id(s), or 'all']"
---

Dispatch a single **verifier** subagent (via the Agent tool, `subagent_type: verifier`) over this
scope:

> $ARGUMENTS

If empty, default to recently-changed and high-confidence-but-unchecked records. The verifier should
resolve the scope to concrete ids by scanning `data/records/`, lock records while checking, and run
its three checks (source reliability, figure↔source factuality, cross-record logical consistency)
per `data/README.md`. On mismatch it lowers confidence and annotates the discrepancy — it never
silently rewrites a value.

When it returns, summarize the verified/flagged list with reasons and any confidence changes.
