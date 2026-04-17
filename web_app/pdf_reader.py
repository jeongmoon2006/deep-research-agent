#!/usr/bin/env python3
"""Download and extract text from paper PDFs for full-text synthesis."""

from __future__ import annotations

import asyncio
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF


# Max pages to read per paper (skip huge appendices)
_MAX_PAGES = 15
# Max chars of extracted text per paper (keeps context window manageable)
_MAX_CHARS = 8000
# Download timeout in seconds
_DOWNLOAD_TIMEOUT = 20
# Max concurrent downloads
_MAX_CONCURRENT = 5


def _get_pdf_url(paper: dict) -> str:
    """Extract the best PDF URL from a paper dict."""
    # arXiv papers
    url = paper.get("pdf_url", "")
    if url:
        return url
    # Semantic Scholar papers
    url = paper.get("openAccessPdfUrl", "")
    if url:
        return url
    # Try to build from arXiv ID
    arxiv_id = paper.get("arxiv_id") or paper.get("arxivId", "")
    if arxiv_id:
        return f"https://arxiv.org/pdf/{arxiv_id}"
    return ""


def _download_and_extract(url: str) -> str | None:
    """Download a PDF and extract text. Returns None on failure."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "deep-research-agent/1.0"},
        )
        with urllib.request.urlopen(req, timeout=_DOWNLOAD_TIMEOUT) as resp:
            pdf_bytes = resp.read()

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages_to_read = min(len(doc), _MAX_PAGES)

        text_parts: list[str] = []
        total_chars = 0
        for page_num in range(pages_to_read):
            page = doc[page_num]
            page_text = page.get_text().strip()
            text_parts.append(page_text)
            total_chars += len(page_text)
            if total_chars >= _MAX_CHARS:
                break

        doc.close()
        full_text = "\n\n".join(text_parts)
        return full_text[:_MAX_CHARS] if full_text.strip() else None
    except Exception:
        return None


async def fetch_paper_texts(
    papers: list[dict],
    max_papers: int = 10,
    on_progress: Any = None,
) -> dict[str, str]:
    """Download and extract full text for the top papers.

    Args:
        papers: Ranked list of paper dicts (top first).
        max_papers: How many papers to attempt downloading.
        on_progress: Optional async callback(downloaded, total, title).

    Returns:
        Dict mapping normalized title → extracted text.
    """
    # Collect papers that have a PDF URL
    to_fetch: list[tuple[str, str, str]] = []  # (title, url, norm_title)
    for p in papers:
        if len(to_fetch) >= max_papers:
            break
        url = _get_pdf_url(p)
        if not url:
            continue
        title = p.get("title", "Untitled")
        norm = " ".join(title.lower().split())
        to_fetch.append((title, url, norm))

    if not to_fetch:
        return {}

    results: dict[str, str] = {}
    semaphore = asyncio.Semaphore(_MAX_CONCURRENT)
    done_count = 0

    async def _fetch_one(title: str, url: str, norm: str) -> None:
        nonlocal done_count
        async with semaphore:
            text = await asyncio.to_thread(_download_and_extract, url)
            done_count += 1
            if text:
                results[norm] = text
            if on_progress:
                await on_progress(done_count, len(to_fetch), title)

    tasks = [_fetch_one(t, u, n) for t, u, n in to_fetch]
    await asyncio.gather(*tasks, return_exceptions=True)

    return results
