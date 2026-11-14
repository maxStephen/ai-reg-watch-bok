"""Convert fetched HTML or PDF into stable plain text."""

from __future__ import annotations

import io
import re

from bs4 import BeautifulSoup
from pypdf import PdfReader

# Page furniture that changes independently of the content we care about.
_STRIP_TAGS = ["script", "style", "noscript", "nav", "header", "footer", "aside", "form", "iframe", "svg"]


def html_to_text(content: bytes) -> str:
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(_STRIP_TAGS):
        tag.decompose()
    root = soup.find("main") or soup.body or soup
    return _clean(root.get_text("\n"))


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
