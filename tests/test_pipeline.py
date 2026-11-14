import httpx
import pytest

from regwatch.config import Source
from regwatch.fetch import Fetcher
from regwatch.pipeline import run
from regwatch.state import State

OPEN = Source("open", "Open Source", "https://open.example/page", "html", ai_allowed=True, store_text=True)
ISO = Source("iso", "Fingerprint Only", "https://iso.example/std", "html", ai_allowed=False, store_text=False)


class Site:
    """Mutable fake web server behind httpx.MockTransport."""

    def __init__(self):
        self.pages: dict[str, tuple[int, bytes]] = {}
        self.robots: dict[str, str] = {}

    def handler(self, request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if request.url.path == "/robots.txt":
            body = self.robots.get(request.url.host)
            return httpx.Response(200, text=body) if body else httpx.Response(404)
        status, body = self.pages.get(url, (404, b""))
        return httpx.Response(status, content=body)

    def page(self, url: str, main: str, status: int = 200):
        self.pages[url] = (status, f"<html><body><main>{main}</main></body></html>".encode())


@pytest.fixture
def site():
    return Site()


@pytest.fixture
def fetcher(site):
    return Fetcher(httpx.Client(transport=httpx.MockTransport(site.handler)))


@pytest.fixture
def state(tmp_path):
    (tmp_path / "snap").mkdir()
    return State(tmp_path / "state.db", tmp_path / "snap")


def statuses(outcomes):
    return {o.source.id: o.status for o in outcomes}


def test_first_run_baseline_then_unchanged(site, fetcher, state):
    site.page(OPEN.url, "<p>Rule A</p>")
    assert statuses(run([OPEN], fetcher, state)) == {"open": "baseline"}
    assert statuses(run([OPEN], fetcher, state)) == {"open": "unchanged"}


def test_substantive_change_produces_diff(site, fetcher, state):
    site.page(OPEN.url, "<p>Rule A</p>")
    run([OPEN], fetcher, state)
    site.page(OPEN.url, "<p>Rule B</p>")
    [outcome] = run([OPEN], fetcher, state)
    assert outcome.status == "changed"
    assert "-Rule A" in outcome.diff and "+Rule B" in outcome.diff
    assert outcome.change_id is not None


def test_date_only_change_is_ignored(site, fetcher, state):
    site.page(OPEN.url, "<p>Rule A</p><p>Updated March 5, 2026</p>")
    run([OPEN], fetcher, state)
    site.page(OPEN.url, "<p>Rule A</p><p>Updated September 24, 2026</p>")
    assert statuses(run([OPEN], fetcher, state)) == {"open": "unchanged"}


def test_fingerprint_only_source_stores_no_text(site, fetcher, state, tmp_path):
    site.page(ISO.url, "<p>Edition 1</p>")
    run([ISO], fetcher, state)
    site.page(ISO.url, "<p>Edition 2</p>")
    [outcome] = run([ISO], fetcher, state)
    assert outcome.status == "changed"
    assert outcome.diff is None
    assert list((tmp_path / "snap").iterdir()) == []
    row = state.conn.execute("SELECT diff FROM changes").fetchone()
    assert row == (None,)


def test_dry_run_saves_nothing(site, fetcher, state):
    site.page(OPEN.url, "<p>Rule A</p>")
    assert statuses(run([OPEN], fetcher, state, dry_run=True)) == {"open": "baseline"}
    assert statuses(run([OPEN], fetcher, state, dry_run=True)) == {"open": "baseline"}
    assert state.get("open").fingerprint is None


def test_blocked_source_does_not_stop_others(site, fetcher, state):
    site.page(ISO.url, "<p>x</p>", status=403)
    site.page(OPEN.url, "<p>Rule A</p>")
    assert statuses(run([ISO, OPEN], fetcher, state)) == {"iso": "blocked", "open": "baseline"}


def test_blocked_fetch_keeps_previous_fingerprint(site, fetcher, state):
    site.page(OPEN.url, "<p>Rule A</p>")
    run([OPEN], fetcher, state)
    fp = state.get("open").fingerprint
    site.page(OPEN.url, "<p>x</p>", status=403)
    run([OPEN], fetcher, state)
    assert state.get("open").fingerprint == fp


def test_robots_disallow_is_honored(site, fetcher, state):
    site.robots["open.example"] = "User-agent: *\nDisallow: /page\n"
    site.page(OPEN.url, "<p>Rule A</p>")
    [outcome] = run([OPEN], fetcher, state)
    assert outcome.status == "blocked" and "robots" in outcome.detail
