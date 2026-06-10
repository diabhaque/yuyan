"""CLI: uv run -m pipelines.nowcast [fetch | process | model | all]."""

import sys

from . import loaders, model, processor


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("fetch", "all"):
        print("[fetch] raw -> data/raw/nowcast/")
        loaders.fetch()
    if cmd in ("process", "all"):
        print("[process] -> data/processed/nowcast/")
        processor.process()
    if cmd in ("model", "all"):
        print("[model] nowcast ->")
        model.run()
    if cmd not in ("fetch", "process", "model", "all"):
        print(f"unknown command {cmd!r}; use fetch | process | model | all")
        sys.exit(1)


if __name__ == "__main__":
    main()
