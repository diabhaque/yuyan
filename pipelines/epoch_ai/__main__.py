"""CLI: uv run -m pipelines.epoch_ai [list | run <slug> | run-all]."""

import sys

from . import ingest, manifest
from .datasets import ALL, get


def _summary(results: list[dict]) -> None:
    print("\n=== Epoch AI ingestion summary ===")
    for r in results:
        print(f"  {r['status']:7} {r['slug']:28} {r['csv_files']:>2} csv  "
              f"{r['rows']:>7} rows  {r['note']}".rstrip())
    ok = sum(r["status"] == "ok" for r in results)
    print(f"{ok}/{len(results)} ok, "
          f"{sum(r['status'] == 'empty' for r in results)} empty, "
          f"{sum(r['status'] == 'failed' for r in results)} failed")


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run-all"

    if cmd == "list":
        for d in ALL:
            print(f"{d.slug:28} {d.kind:7} {d.name}")
        return

    if cmd == "run":
        targets = [get(sys.argv[2])]
    elif cmd == "run-all":
        targets = ALL
    else:
        print(f"unknown command {cmd!r}; use list | run <slug> | run-all")
        sys.exit(1)

    manifest.write()  # pre-download manifest
    results = ingest.run(targets)
    manifest.write({r["slug"]: r["bytes"] for r in results})  # update sizes
    _summary(results)


if __name__ == "__main__":
    main()
