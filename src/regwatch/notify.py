"""macOS notification. Clicking it opens the digest when terminal-notifier is installed."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from urllib.parse import quote

log = logging.getLogger(__name__)

TITLE = "AI Regulation Watch"


def obsidian_url(vault: Path, note: str) -> str:
    return f"obsidian://open?vault={quote(vault.name)}&file={quote(note)}"


def command(message: str, open_url: str | None, notifier: str | None) -> list[str]:
    if notifier:
        cmd = [notifier, "-title", TITLE, "-message", message, "-group", "regwatch"]
        if open_url:
            cmd += ["-open", open_url]
        return cmd
    # Fallback: built-in notification (clicking it cannot open Obsidian).
    script = f"display notification {_applescript_str(message)} with title {_applescript_str(TITLE)}"
    return ["osascript", "-e", script]


def _applescript_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def send(message: str, vault: Path, digest: str | None) -> None:
    notifier = shutil.which("terminal-notifier")
    url = obsidian_url(vault, digest) if digest else None
    result = subprocess.run(command(message, url, notifier), capture_output=True, text=True)
    if result.returncode != 0:
        log.warning("Notification failed: %s", result.stderr.strip())
