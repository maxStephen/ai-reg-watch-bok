"""The one-line summary shared by the console, the digest, and the notification."""

from __future__ import annotations

from .pipeline import Outcome

PROBLEM_STATUSES = ("blocked", "error")


def changed(outcomes: list[Outcome]) -> list[Outcome]:
    return [o for o in outcomes if o.status == "changed"]


def problems(outcomes: list[Outcome]) -> list[Outcome]:
    return [o for o in outcomes if o.status in PROBLEM_STATUSES]


def manual(outcomes: list[Outcome]) -> list[Outcome]:
    return [o for o in outcomes if o.status == "manual"]


def headline(outcomes: list[Outcome]) -> str:
    n = len(changed(outcomes))
    text = f"{n or 'No'} AI regulation change{'' if n == 1 else 's'}"
    p = len(problems(outcomes))
    if p:
        text += f"; {p} source{'' if p == 1 else 's'} need{'s' if p == 1 else ''} attention"
    return text
