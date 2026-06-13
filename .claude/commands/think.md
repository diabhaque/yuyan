---
description: Run the Thinker agent standalone — decompose a goal into a metric graph and write proposal records (confidence 0) for what's missing.
argument-hint: "<goal>"
---

Dispatch a single **thinker** subagent (via the Agent tool, `subagent_type: thinker`) with this goal:

> $ARGUMENTS

The thinker should: understand the goal, scan `data/records/` for what already exists, design the
metric graph, and write proposal records (`confidence: 0`, placeholder value + units, `inputs`/
`adjacency` edges) for whatever is missing — following `data/README.md` and using the
`data/records/_locks.json` lock protocol. Do not have it chase real values.

When it returns, summarize the proposed record ids and the graph it laid down.
