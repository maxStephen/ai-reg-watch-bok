"""Command-line entry point: `regwatch run [--dry-run]`."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date

from .config import load_paths, load_sources
from .fetch import Fetcher
from .pipeline import run
from .state import State


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="regwatch")
    sub = parser.add_subparsers(dest="command", required=True)
    run_p = sub.add_parser("run", help="check all sources once")
    run_p.add_argument("--dry-run", action="store_true", help="fetch and compare, but save nothing")
    args = parser.parse_args(argv)

    paths = load_paths()
    paths.ensure()
    handlers = [logging.StreamHandler(sys.stdout)]
    if not args.dry_run:
        handlers.append(logging.FileHandler(paths.logs / f"{date.today():%Y-%m}.log"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=handlers)

    logging.getLogger("httpx").setLevel(logging.WARNING)

    state = State(paths.db, paths.snapshots)
    outcomes = run(load_sources(), Fetcher(), state, dry_run=args.dry_run)

    changed = [o for o in outcomes if o.status == "changed"]
    problems = [o for o in outcomes if o.status in ("blocked", "error")]
    print(f"\n{len(changed) or 'No'} AI regulation change{'' if len(changed) == 1 else 's'}"
          + (f"; {len(problems)} source(s) need attention" if problems else "")
          + (" (dry run, nothing saved)" if args.dry_run else ""))
    for o in changed:
        print(f"\n## {o.source.name}\n{o.diff or '(fingerprint-only source: review manually at ' + o.source.url + ')'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
