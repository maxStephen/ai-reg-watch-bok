"""Source definitions and local paths."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SOURCES = REPO_DIR / "config" / "sources.yaml"

# Local-only data (logs, state, secrets) lives in a sibling folder, never in the repo.
DEFAULT_HOME = REPO_DIR.parent / f"{REPO_DIR.name}.local"
DEFAULT_VAULT = Path.home() / "Documents" / "vaults" / "ai-audit-bok"

CHECK_MODES = ("daily", "weekly", "manual")  # weekly and manual-reminder days are Mondays


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    url: str
    type: str
    ai_allowed: bool
    store_text: bool
    check: str = "daily"


@dataclass(frozen=True)
class Paths:
    home: Path

    @property
    def logs(self) -> Path:
        return self.home / "logs"

    @property
    def state(self) -> Path:
        return self.home / "state"

    @property
    def db(self) -> Path:
        return self.state / "state.db"

    @property
    def snapshots(self) -> Path:
        return self.state / "snapshots"

    @property
    def secrets(self) -> Path:
        return self.home / "secrets"

    def ensure(self) -> None:
        for d in (self.logs, self.snapshots, self.secrets):
            d.mkdir(parents=True, exist_ok=True)
        self.secrets.chmod(0o700)


def load_paths() -> Paths:
    return Paths(Path(os.environ.get("REGWATCH_HOME", DEFAULT_HOME)).expanduser())


def load_vault() -> Path:
    return Path(os.environ.get("REGWATCH_VAULT", DEFAULT_VAULT)).expanduser()


def load_sources(path: Path = DEFAULT_SOURCES) -> list[Source]:
    data = yaml.safe_load(path.read_text())
    sources = [
        Source(
            id=s["id"],
            name=s["name"],
            url=s["url"],
            type=s["type"],
            ai_allowed=bool(s.get("ai_allowed", False)),
            store_text=bool(s.get("store_text", False)),
            check=s.get("check", "daily"),
        )
        for s in data["sources"]
    ]
    ids = [s.id for s in sources]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate source ids in {path}")
    for s in sources:
        if s.type not in ("html", "pdf"):
            raise ValueError(f"Source {s.id}: unsupported type {s.type!r}")
        if s.check not in CHECK_MODES:
            raise ValueError(f"Source {s.id}: check must be one of {CHECK_MODES}")
    return sources
