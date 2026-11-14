"""Change detection: fingerprints that ignore noise, and readable diffs."""

from __future__ import annotations

import difflib
import hashlib
import re

_MONTHS = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?"
_DATE_PATTERNS = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:?\d{2})?)?\b"),
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),
    re.compile(rf"\b{_MONTHS}\s+\d{{1,2}},?\s+\d{{4}}\b", re.IGNORECASE),
    re.compile(rf"\b\d{{1,2}}\s+{_MONTHS}\s+\d{{4}}\b", re.IGNORECASE),
    re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:[AaPp]\.?[Mm]\.?)?\b"),
]


def canonical(text: str) -> str:
    """Text with date/time stamps masked, so date-only edits don't count as changes."""
    for pattern in _DATE_PATTERNS:
        text = pattern.sub("<DATE>", text)
    return text


def fingerprint(text: str) -> str:
    return hashlib.sha256(canonical(text).encode("utf-8")).hexdigest()


def unified_diff(old: str, new: str, label: str, context: int = 2) -> str:
    return "\n".join(
        difflib.unified_diff(
            old.splitlines(), new.splitlines(),
            fromfile=f"{label} (previous)", tofile=f"{label} (current)",
            n=context, lineterm="",
        )
    )
