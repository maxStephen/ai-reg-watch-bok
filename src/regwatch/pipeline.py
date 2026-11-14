"""One monitoring pass over all sources."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .config import Source
from .detect import fingerprint, unified_diff
from .fetch import Fetcher
from .normalize import normalize
from .state import State

log = logging.getLogger(__name__)


@dataclass
class Outcome:
    source: Source
    status: str  # "baseline" | "unchanged" | "changed" | "not_modified" | "blocked" | "error"
    detail: str = ""
    diff: str | None = None  # None for fingerprint-only sources
    change_id: int | None = None


def check_source(source: Source, fetcher: Fetcher, state: State, dry_run: bool = False) -> Outcome:
    prev = state.get(source.id)
    result = fetcher.fetch(source.url, prev.etag, prev.last_modified)

    if result.status != "ok":
        if not dry_run:
            state.update(source.id, result.status)
        return Outcome(source, result.status, result.detail)

    try:
        text = normalize(result.content, source.type)
    except Exception as e:  # malformed PDF/HTML must not stop the run
        if not dry_run:
            state.update(source.id, "error")
        return Outcome(source, "error", f"normalize failed: {type(e).__name__}: {e}")

    fp = fingerprint(text)

    if prev.fingerprint is None:
        outcome = Outcome(source, "baseline", "first run: recorded baseline")
    elif fp == prev.fingerprint:
        outcome = Outcome(source, "unchanged")
    else:
        diff = None
        if source.store_text:
            old_text = state.read_snapshot(source.id) or ""
            diff = unified_diff(old_text, text, source.name)
        outcome = Outcome(source, "changed", diff=diff)
        if not dry_run:
            outcome.change_id = state.record_change(source.id, prev.fingerprint, fp, diff)

    if not dry_run:
        state.update(source.id, outcome.status, fp, result.etag, result.last_modified)
        if source.store_text:
            state.write_snapshot(source.id, text)
    return outcome


def run(sources: list[Source], fetcher: Fetcher, state: State, dry_run: bool = False) -> list[Outcome]:
    outcomes = []
    for source in sources:
        outcome = check_source(source, fetcher, state, dry_run)
        log.info("%-16s %-12s %s", source.id, outcome.status, outcome.detail)
        outcomes.append(outcome)
    return outcomes
