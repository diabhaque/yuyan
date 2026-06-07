"""CLI: `uv run -m pipelines list` / `uv run -m pipelines run <name>`."""

import argparse

from .registry import REGISTRY, get


def main():
    parser = argparse.ArgumentParser(prog="pipelines")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="list registered pipelines")
    run = sub.add_parser("run", help="run a pipeline by name")
    run.add_argument("name")
    args = parser.parse_args()

    if args.command == "list":
        for name in sorted(REGISTRY):
            print(name)
    elif args.command == "run":
        get(args.name)().run()


if __name__ == "__main__":
    main()
