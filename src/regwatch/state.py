"""Local SQLite state and text snapshots (outside the repo)."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id            TEXT PRIMARY KEY,
    fingerprint   TEXT,
    etag          TEXT,
    last_modified TEXT,
    last_checked  TEXT,
    last_status   TEXT
);
CREATE TABLE IF NOT EXISTS changes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       TEXT NOT NULL,
    detected_at     TEXT NOT NULL,
    old_fingerprint TEXT NOT NULL,
    new_fingerprint TEXT NOT NULL,
    diff            TEXT
);
"""


@dataclass
class SourceState:
    fingerprint: str | None = None
    etag: str | None = None
    last_modified: str | None = None


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class State:
    def __init__(self, db_path: Path, snapshot_dir: Path):
        self.conn = sqlite3.connect(db_path)
        self.conn.executescript(_SCHEMA)
        self.snapshot_dir = snapshot_dir

    def get(self, source_id: str) -> SourceState:
        row = self.conn.execute(
            "SELECT fingerprint, etag, last_modified FROM sources WHERE id = ?", (source_id,)
        ).fetchone()
        return SourceState(*row) if row else SourceState()

    def update(self, source_id: str, status: str, fingerprint: str | None = None,
               etag: str | None = None, last_modified: str | None = None) -> None:
        """Record a check. Fingerprint/validators are only replaced when provided."""
        self.conn.execute(
            """INSERT INTO sources (id, fingerprint, etag, last_modified, last_checked, last_status)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 fingerprint   = COALESCE(excluded.fingerprint, fingerprint),
                 etag          = COALESCE(excluded.etag, etag),
                 last_modified = COALESCE(excluded.last_modified, last_modified),
                 last_checked  = excluded.last_checked,
                 last_status   = excluded.last_status""",
            (source_id, fingerprint, etag, last_modified, now(), status),
        )
        self.conn.commit()

    def record_change(self, source_id: str, old_fp: str, new_fp: str, diff: str | None) -> int:
        cur = self.conn.execute(
            "INSERT INTO changes (source_id, detected_at, old_fingerprint, new_fingerprint, diff) "
            "VALUES (?, ?, ?, ?, ?)",
            (source_id, now(), old_fp, new_fp, diff),
        )
        self.conn.commit()
        return cur.lastrowid

    def read_snapshot(self, source_id: str) -> str | None:
        path = self.snapshot_dir / f"{source_id}.txt"
        return path.read_text() if path.exists() else None

    def write_snapshot(self, source_id: str, text: str) -> None:
        (self.snapshot_dir / f"{source_id}.txt").write_text(text)
