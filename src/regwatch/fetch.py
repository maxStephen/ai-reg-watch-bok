"""Polite HTTP fetching: identifies itself, honors robots.txt, uses conditional requests."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from . import __version__

USER_AGENT = f"ai-reg-watch-bok/{__version__} (+https://github.com/maxStephen/ai-reg-watch-bok)"
TIMEOUT = httpx.Timeout(30.0)


@dataclass
class FetchResult:
    status: str  # "ok" | "not_modified" | "blocked" | "error"
    content: bytes = b""
    etag: str | None = None
    last_modified: str | None = None
    detail: str = ""


class Fetcher:
    def __init__(self, client: httpx.Client | None = None):
        self.client = client or httpx.Client(
            headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT, follow_redirects=True
        )
        self._robots: dict[str, RobotFileParser | None] = {}

    def _allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._robots:
            rp = RobotFileParser()
            try:
                resp = self.client.get(f"{origin}/robots.txt")
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
                    self._robots[origin] = rp
                else:
                    self._robots[origin] = None  # no robots.txt: allowed
            except httpx.HTTPError:
                self._robots[origin] = None
        rp = self._robots[origin]
        return rp is None or rp.can_fetch(USER_AGENT, url)

    def fetch(self, url: str, etag: str | None = None, last_modified: str | None = None) -> FetchResult:
        if not self._allowed(url):
            return FetchResult("blocked", detail="disallowed by robots.txt")
        headers = {}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        try:
            resp = self.client.get(url, headers=headers)
        except httpx.HTTPError as e:
            return FetchResult("error", detail=f"{type(e).__name__}: {e}")
        if resp.status_code == 304:
            return FetchResult("not_modified", etag=etag, last_modified=last_modified)
        if resp.status_code in (401, 403, 429):
            return FetchResult("blocked", detail=f"HTTP {resp.status_code}")
        if resp.status_code != 200:
            return FetchResult("error", detail=f"HTTP {resp.status_code}")
        return FetchResult(
            "ok",
            content=resp.content,
            etag=resp.headers.get("ETag"),
            last_modified=resp.headers.get("Last-Modified"),
        )
