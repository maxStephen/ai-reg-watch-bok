"""Command-line entry point: `regwatch run [--dry-run] [--no-notify] [--date YYYY-MM-DD]`."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date

from . import notify, report, vault
from .config import load_paths, load_sources, load_vault
from .fetch import Fetcher
from .pipeline import run
from .state import State


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="regwatch")
    sub = parser.add_subparsers(dest="command", required=True)
    run_p = sub.add_parser("run", help="check all sources once")
    run_p.add_argument("--dry-run", action="store_true",
                       help="fetch and compare, but save nothing, write no notes, send no notification")
    run_p.add_argument("--no-notify", action="store_true", help="skip the macOS notification")
    run_p.add_argument("--date", type=date.fromisoformat, default=None,
                       help="treat this as today's date (for testing weekly/manual schedules)")
    args = parser.parse_args(argv)
    today = args.date or date.today()

    paths = load_paths()
    paths.ensure()
    handlers = [logging.StreamHandler(sys.stdout)]
    if not args.dry_run:
        handlers.append(logging.FileHandler(paths.logs / f"{today:%Y-%m}.log"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=handlers)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    state = State(paths.db, paths.snapshots)
    outcomes = run(load_sources(), Fetcher(), state, dry_run=args.dry_run, today=today)
    headline = report.headline(outcomes)

    if args.dry_run:
        print(f"\n{headline} (dry run, nothing saved)")
        for o in report.changed(outcomes):
            print(f"\n## {o.source.name}\n{o.diff or '(fingerprint-only source: review manually at ' + o.source.url + ')'}")
        for o in report.manual(outcomes):
            print(f"Manual check: {o.source.name}: {o.source.url}")
        return 0

    vault_dir = load_vault()
    digest = vault.write(outcomes, vault_dir, today)
    if digest:
        vault.commit(vault_dir, f"Regulation Watch {today:%Y-%m-%d}: {headline}")
    if not args.no_notify:
        notify.send(headline, vault_dir, digest)
    logging.info("%s%s", headline, f" (digest: {digest})" if digest else "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
