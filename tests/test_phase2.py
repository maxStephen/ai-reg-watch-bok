import subprocess
from datetime import date
from pathlib import Path

from regwatch import notify, report, vault
from regwatch.config import Source
from regwatch.pipeline import Outcome, run

MONDAY = date(2026, 11, 16)
TUESDAY = date(2026, 11, 17)

OPEN = Source("open", "Open Source", "https://open.example/page", "html", True, True)
ISO = Source("iso", "ISO Thing", "https://iso.example/std", "html", False, False, check="manual")
WEEKLY = Source("wk", "Weekly Thing", "https://wk.example/p", "html", True, True, check="weekly")


class NoFetch:
    def fetch(self, *a, **k):
        raise AssertionError("must not fetch")


# --- headline ---------------------------------------------------------------

def test_headline_wording():
    ch = Outcome(OPEN, "changed", diff="x")
    bad = Outcome(OPEN, "blocked", "HTTP 403")
    assert report.headline([]) == "No AI regulation changes"
    assert report.headline([ch]) == "1 AI regulation change"
    assert report.headline([ch, ch]) == "2 AI regulation changes"
    assert report.headline([bad]) == "No AI regulation changes; 1 source needs attention"
    assert report.headline([bad, bad]) == "No AI regulation changes; 2 sources need attention"


# --- scheduling -------------------------------------------------------------

def test_manual_source_is_never_fetched_and_reminds_on_monday():
    assert run([ISO], NoFetch(), state=None, today=TUESDAY) == []
    [o] = run([ISO], NoFetch(), state=None, today=MONDAY)
    assert o.status == "manual"


def test_weekly_source_skipped_except_monday():
    assert run([WEEKLY], NoFetch(), state=None, today=TUESDAY) == []


# --- vault ------------------------------------------------------------------

def test_no_content_writes_nothing(tmp_path):
    assert vault.write([Outcome(OPEN, "unchanged")], tmp_path, TUESDAY) is None
    assert list(tmp_path.iterdir()) == []


def test_change_writes_inbox_note_and_digest(tmp_path):
    o = Outcome(OPEN, "changed", diff="-old\n+new", change_id=7)
    digest = vault.write([o], tmp_path, TUESDAY)
    assert digest == "Regulation Watch/Digests/2026-11-17"
    note = (tmp_path / "Regulation Watch/Inbox/2026-11-17 open.md").read_text()
    assert "status: new" in note and "change_id: 7" in note and "```diff\n-old\n+new\n```" in note
    text = (tmp_path / f"{digest}.md").read_text()
    assert "**1 AI regulation change**" in text
    assert "[[Regulation Watch/Inbox/2026-11-17 open]]" in text


def test_digest_lists_problems_and_manual_checks(tmp_path):
    outcomes = [Outcome(OPEN, "error", "HTTP 500"), Outcome(ISO, "manual")]
    digest = vault.write(outcomes, tmp_path, MONDAY)
    text = (tmp_path / f"{digest}.md").read_text()
    assert "## Needs attention" in text and "HTTP 500" in text
    assert "## Manual checks this week" in text and "- [ ] ISO Thing" in text


def test_long_diff_truncated_in_digest_only(tmp_path):
    diff = "\n".join(f"+line {i}" for i in range(vault.DIGEST_DIFF_LINES + 50))
    digest = vault.write([Outcome(OPEN, "changed", diff=diff)], tmp_path, TUESDAY)
    assert "truncated" in (tmp_path / f"{digest}.md").read_text()
    assert "+line 249" in (tmp_path / "Regulation Watch/Inbox/2026-11-17 open.md").read_text()


def test_fence_survives_backticks_in_diff():
    assert vault.fence("+use ``` here").startswith("````diff")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def test_commit_only_touches_regulation_watch_folder(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "Index.md").write_text("draft in progress")
    vault.write([Outcome(OPEN, "changed", diff="+x")], tmp_path, TUESDAY)
    vault.commit(tmp_path, "msg", push=False)
    committed = _git(tmp_path, "show", "--name-only", "--format=", "HEAD").split("\n")
    assert all(f.startswith("Regulation Watch/") for f in committed if f)
    assert "?? Index.md" in _git(tmp_path, "status", "--short")


# --- notification -----------------------------------------------------------

def test_obsidian_url_encodes_vault_and_note():
    url = notify.obsidian_url(Path("/x/ai-audit-bok"), "Regulation Watch/Digests/2026-11-17")
    assert url == "obsidian://open?vault=ai-audit-bok&file=Regulation%20Watch/Digests/2026-11-17"


def test_terminal_notifier_command_opens_digest():
    cmd = notify.command("No AI regulation changes", "obsidian://x", "/opt/homebrew/bin/terminal-notifier")
    assert cmd[-2:] == ["-open", "obsidian://x"] and "No AI regulation changes" in cmd


def test_osascript_fallback_escapes_quotes():
    cmd = notify.command('say "hi"', None, None)
    assert cmd[0] == "osascript" and 'say \\"hi\\"' in cmd[2]
