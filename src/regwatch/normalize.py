"""Convert fetched HTML or PDF into stable plain text."""

from __future__ import annotations

import io
import re

from bs4 import BeautifulSoup, NavigableString
from pypdf import PdfReader

# Page furniture that changes independently of the content we care about.
_STRIP_TAGS = ["script", "style", "noscript", "nav", "header", "footer", "aside", "form", "iframe", "svg"]
_STRIP_SELECTORS = ".usa-banner, .usa-skipnav, [class*=skip-link], a[href=\"#main-content\"], [class*=breadcrumb], [class*=cookie], [id*=cookie]"

# Elements that start a new line; everything else (links, emphasis, spans) stays inline.
_BLOCK_TAGS = [
    "address", "article", "blockquote", "dd", "div", "dl", "dt", "figcaption", "figure",
    "h1", "h2", "h3", "h4", "h5", "h6", "hr", "li", "main", "ol", "p", "pre", "section",
    "table", "td", "th", "tr", "ul",
]


def html_to_text(content: bytes) -> str:
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(_STRIP_TAGS):
        tag.decompose()
    for tag in soup.select(_STRIP_SELECTORS):
        tag.decompose()
    root = soup.find("main") or soup.body or soup
    # Source-code line breaks are just whitespace; collapse them before adding real ones.
    for s in list(root.find_all(string=True)):
        if type(s) is NavigableString:  # leaves comments and other subclasses alone
            s.replace_with(re.sub(r"\s+", " ", s))
    for br in root.find_all("br"):
        br.replace_with("\n")
    for tag in root.find_all(_BLOCK_TAGS):
        tag.insert_before("\n")
        tag.insert_after("\n")
    return _clean(root.get_text(""))


def pdf_to_text(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    return _clean("\n".join(page.extract_text() or "" for page in reader.pages))


def normalize(content: bytes, source_type: str) -> str:
    if source_type == "pdf":
        return pdf_to_text(content)
    return html_to_text(content)


def _clean(text: str) -> str:
    lines = (re.sub(r"\s+", " ", line).strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)
