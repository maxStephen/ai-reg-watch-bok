"""Write Inbox notes and a dated digest into the Obsidian vault, then commit them."""

from __future__ import annotations

import logging
import re
import subprocess
from datetime import date
from pathlib import Path

from . import report
from .pipeline import Outcome

log = logging.getLogger(__name__)

ROOT = "Regulation Watch"
INBOX = f"{ROOT}/Inbox"
DIGESTS = f"{ROOT}/Digests"
DIGEST_DIFF_LINES = 200  # longer diffs are shown in full only in the Inbox note


def fence(text: str, lang: str = "diff") -> str:
    """A code fence longer than any backtick run inside the text."""
    longest = max((len(m) for m in re.findall(r"`+", text)), default=0)
    ticks = "`" * max(3, longest + 1)
    return f"{ticks}{lang}\n{text}\n{ticks}"


def _truncate(diff: str) -> tuple[str, bool]:
    lines = diff.splitlines()
    if len(lines) <= DIGEST_DIFF_LINES:
        return diff, False
    return "\n".join(lines[:DIGEST_DIFF_LINES]), True


def inbox_note_name(o: Outcome, today: date) -> str:
    return f"{today:%Y-%m-%d} {o.source.id}"


def digest_path(today: date) -> str:
    return f"{DIGESTS}/{today:%Y-%m-%d}"


def render_inbox_note(o: Outcome, today: date) -> str:
    lines = [
        "---",
        f'source: "{o.source.name}"',
        f"source_id: {o.source.id}",
        f"url: {o.source.url}",
        f"detected: {today:%Y-%m-%d}",
        f"change_id: {o.change_id}",
        "status: new",
        f"ai_allowed: {str(o.source.ai_allowed).lower()}",
        "tags: [regwatch]",
        "---",
        "",
        f"# {o.source.name}",
        "",
        f"Detected {today:%Y-%m-%d}. Digest: [[{digest_path(today)}]]. Source: {o.source.url}",
        "",
        "## Changes",
        "",
    ]
    if o.diff:
        lines.append(fence(o.diff))
    else:
        lines.append("Fingerprint-only source: no text is stored. Review the source manually.")
    lines += ["", "## Review notes", "", "- Link to: [[Frameworks]] / [[Questions and Recommendations]]", ""]
    return "\n".join(lines)


def render_digest(outcomes: list[Outcome], today: date) -> str:
    lines = [
        "---",
        f"date: {today:%Y-%m-%d}",
        "tags: [regwatch, digest]",
        "---",
        "",
        f"# AI Regulation Watch: {today:%Y-%m-%d}",
        "",
        f"**{report.headline(outcomes)}**",
        "",
    ]
    for o in report.changed(outcomes):
        lines += [f"## {o.source.name}", "", f"Note: [[{INBOX}/{inbox_note_name(o, today)}]] · {o.source.url}", ""]
        if o.diff:
            shown, cut = _truncate(o.diff)
            lines.append(fence(shown))
            if cut:
                lines.append(f"\n*Diff truncated to {DIGEST_DIFF_LINES} lines; full diff in the Inbox note.*")
        else:
            lines.append("Fingerprint-only source: review manually.")
        lines.append("")
    if report.problems(outcomes):
        lines += ["## Needs attention", ""]
        lines += [f"- **{o.source.name}**: {o.status} ({o.detail}) · {o.source.url}" for o in report.problems(outcomes)]
        lines.append("")
    if report.manual(outcomes):
        lines += ["## Manual checks this week", ""]
        lines += [f"- [ ] {o.source.name}: {o.source.url}" for o in report.manual(outcomes)]
        lines.append("")
    return "\n".join(lines)


def has_digest_content(outcomes: list[Outcome]) -> bool:
    return bool(report.changed(outcomes) or report.problems(outcomes) or report.manual(outcomes))


def write(outcomes: list[Outcome], vault: Path, today: date) -> str | None:
    """Write notes. Returns the digest's vault-relative path (no .md), or None if nothing to write."""
    if not has_digest_content(outcomes):
        return None
    (vault / INBOX).mkdir(parents=True, exist_ok=True)
    (vault / DIGESTS).mkdir(parents=True, exist_ok=True)
    for o in report.changed(outcomes):
        (vault / INBOX / f"{inbox_note_name(o, today)}.md").write_text(render_inbox_note(o, today))
    (vault / f"{digest_path(today)}.md").write_text(render_digest(outcomes, today))
    return digest_path(today)


def commit(vault: Path, message: str, push: bool = True) -> None:
    """Commit only the Regulation Watch folder, so in-progress edits elsewhere are untouched."""
    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(vault), *args], capture_output=True, text=True)

    if git("rev-parse", "--is-inside-work-tree").returncode != 0:
        log.warning("Vault is not a git repository; skipping commit")
        return
    git("add", "--", ROOT)
    if git("diff", "--cached", "--quiet", "--", ROOT).returncode == 0:
        return
    result = git("commit", "-m", message, "--", ROOT)
    if result.returncode != 0:
        log.warning("Vault commit failed: %s", result.stderr.strip())
        return
    if push:
        result = git("push", "--quiet")
        if result.returncode != 0:
            log.warning("Vault push failed (will go out with the next push): %s", result.stderr.strip())
