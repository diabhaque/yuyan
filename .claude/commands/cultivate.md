---
description: Dynamic orchestrator — sense the datastore's state and dispatch Thinker/Builder/Verifier/Organizer agents in state-driven cycles until the goal converges or a cycle cap is hit.
argument-hint: "<goal> [--max-cycles N]"
---

You are the **cultivation orchestrator** for the `yuyan` record datastore. Run on the main thread
(subagents cannot spawn subagents). Parse the argument into a **goal** and an optional
`--max-cycles N` (default **5**).

> $ARGUMENTS

Read `data/README.md` once for the envelope, the `inputs ↔ adjacency` invariant, and the
`data/records/_locks.json` protocol. Then loop the four steps below. This is **dynamic**: which
agents you dispatch each cycle depends on what SENSE reports — there is no fixed pipeline.

## 1. SENSE — snapshot the datastore (ad-hoc, no committed script)
Run this fresh each cycle and read its JSON output. It walks the records, skips `_*` files, and
reports the state you reason over:

```bash
uv run python - <<'PY'
import json, glob, datetime
recs, by_id = [], {}
for p in glob.glob("data/records/**/*.json", recursive=True):
    if "/_" in p or p.split("/")[-1].startswith("_"): continue
    r = json.load(open(p)); r["_path"] = p; recs.append(r); by_id[r["id"]] = r
def deg(r): return len(r.get("methodology",{}).get("inputs",[])) + len(r.get("adjacency",[]))
counts = {}
for r in recs: counts[r["type"]] = counts.get(r["type"],0)+1
proposed = [r["id"] for r in recs if r.get("confidence",0)==0]
queue = sorted([r for r in recs if r.get("confidence",1) < 0.5],
               key=lambda r:(r.get("confidence",0), -deg(r)))
orphans = [r["id"] for r in recs if deg(r)==0]
viol = []
for r in recs:
    for i in r.get("methodology",{}).get("inputs",[]):
        if i in by_id and r["id"] not in by_id[i].get("adjacency",[]): viol.append(f"{r['id']}.inputs->{i} but not in {i}.adjacency")
    for a in r.get("adjacency",[]):
        if a in by_id and r["id"] not in by_id[a].get("methodology",{}).get("inputs",[]): viol.append(f"{r['id']}.adjacency->{a} but not in {a}.inputs")
try: locks = json.load(open("data/records/_locks.json"))
except FileNotFoundError: locks = {}
print(json.dumps({
  "total": len(recs), "counts_by_type": counts,
  "proposed_conf0": proposed,
  "priority_queue": [{"id":r["id"],"confidence":r.get("confidence"),"degree":deg(r),"tags":r.get("tags")} for r in queue[:15]],
  "orphans": orphans, "invariant_violations": viol, "active_locks": locks,
}, indent=2))
PY
```

Also judge **goal coverage**: do records exist whose tags/description match the goal? (Grep the goal's
key terms over `data/records/`.)

## 2. DECIDE — choose agents from the snapshot (state-driven branching)
- **Coverage gap** (few/no records on the goal topic, or no metric graph for it) → dispatch a
  **thinker** with the goal.
- **Non-empty priority queue** → dispatch **builder(s)** on the top targets. Partition the chosen
  targets into **disjoint id sets** (one set per builder) so parallel builders never contend for the
  same lock.
- **Changed or unchecked values** (records built/edited recently, or high confidence with no
  `verified` note) → dispatch a **verifier** over them.
- **Structural issues** (any `invariant_violations`, orphans, duplicates, or weak tags above a small
  threshold) → dispatch an **organizer**.

Skip any record that is currently held in `active_locks` (unless its lock is stale per its
`ttl_minutes`). A natural early cycle is Thinker → Builders, with Verifier/Organizer following once
values exist — but always let the snapshot drive the choice.

## 3. ACT — dispatch
Spawn the chosen subagents via the Agent tool (`subagent_type` = `thinker`/`builder`/`verifier`/
`organizer`), giving each its goal/target ids/scope. Run lock-disjoint agents **in parallel** (one
message, multiple Agent calls). Each agent follows the lock protocol itself.

## 4. INTEGRATE & LOOP
Re-run SENSE. Append one line to `data/records/_cultivate_log.jsonl`:
`{"ts": "...", "cycle": N, "goal": "...", "dispatched": [...], "result": "<one-line>"}`.
Summarize the cycle to the user.

**Stop** when **converged** — goal is covered, the priority queue is empty among goal-relevant nodes,
and there are no invariant violations / structural issues — **or** when `--max-cycles` is reached.
Report the final state and what (if anything) still needs attention.
