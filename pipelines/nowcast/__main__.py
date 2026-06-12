"""CLI: uv run -m pipelines.nowcast [fetch | process | model | all]."""

import sys

from . import config, loaders, model, processor


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("fetch", "all"):
        print("[fetch] raw -> data/raw/nowcast/")
        loaders.fetch()
    if cmd in ("process", "all"):
        print("[process] -> data/processed/nowcast/")
        processor.process()
    if cmd in ("model", "all"):
        print("[model] targets (chained):")
        for target in config.RUN_ORDER:  # Q1 nowcast before Q2 forecast (chaining)
            model.run(target)
    if cmd not in ("fetch", "process", "model", "all"):
        print(f"unknown command {cmd!r}; use fetch | process | model | all")
        sys.exit(1)


if __name__ == "__main__":
    main()
