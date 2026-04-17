#!/usr/bin/env python3
"""Research orchestration — paper discovery, scoring, and LLM synthesis."""

from __future__ import annotations

import asyncio
import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

# Import tool functions directly (arXiv and Semantic Scholar search/scoring)
_TOOLS_DIR = Path(__file__).parent.parent / "tools"
sys.path.insert(0, str(_TOOLS_DIR))

from arxiv_server import search_arxiv  # type: ignore[import]
from semantic_scholar_server import search_semantic_scholar, score_papers  # type: ignore[import]

from .providers import complete, stream_completion

# Type alias for the emit callback:  await emit("event_type", key=value, ...)
EmitFn = Callable[..., Any]

_REPORTS_DIR = Path(__file__).parent.parent / "reports"
_CURRENT_YEAR = 2026


async def run_research(
    topic: str,
    provider: str,
    api_key: str,
    model: str,
    emit: EmitFn,
) -> str:
    """Run the full research pipeline and write the final report.

    Args:
        topic: Research topic to survey.
        provider: LLM provider ("openai" or "anthropic").
        api_key: Provider API key.
        model: Model name.
        emit: Async callable that sends SSE events: await emit(type, **data).

    Returns:
        Final report markdown as a string.
    """
    # 1. Generate targeted search queries via LLM
    await emit("status", message="Generating search queries…")
    queries = await _generate_queries(topic, provider, api_key, model)
    await emit("queries", queries=queries,
               message="Generated {} search queries".format(len(queries)))

    # 2. Collect paper candidates from arXiv and Semantic Scholar
    all_papers: list[dict] = []
    seen_titles: set[str] = set()

    for q in queries:
        await emit("status", message=f"Searching arXiv — {q}")
        try:
            arxiv_results = await asyncio.to_thread(search_arxiv, q, 40)
            new_papers = _deduplicate(arxiv_results, seen_titles, "arXiv")
            all_papers.extend(new_papers)
            await emit("papers_found", source="arXiv", query=q,
                       new=len(new_papers), total=len(all_papers))
        except Exception as exc:
            await emit("warning", message=f"arXiv search failed for '{q}': {exc}")

        await emit("status", message=f"Searching Semantic Scholar — {q}")
        try:
            ss_results = await asyncio.to_thread(search_semantic_scholar, q, 40)
            new_papers = _deduplicate(ss_results, seen_titles, "Semantic Scholar")
            all_papers.extend(new_papers)
            await emit("papers_found", source="Semantic Scholar", query=q,
                       new=len(new_papers), total=len(all_papers))
        except Exception as exc:
            await emit("warning", message=f"Semantic Scholar search failed for '{q}': {exc}")

    if not all_papers:
        await emit("error", message="No papers found. Try a different topic or check your network.")
        return ""

    # 3. Score and rank candidates
    await emit("status", message=f"Scoring {len(all_papers)} candidates…")
    scored = await asyncio.to_thread(score_papers, all_papers)
    top_papers = scored[:100]
    top_title = top_papers[0].get("title", "") if top_papers else ""
    await emit("papers_scored", total=len(scored), kept=len(top_papers), top_paper=top_title)

    # 4. Synthesize report via LLM (streaming)
    await emit("status", message=f"Synthesizing report from top {len(top_papers)} papers…")
    await emit("synthesis_start")

    report_chunks: list[str] = []
    async for chunk in _synthesize(topic, top_papers, provider, api_key, model, emit):
        report_chunks.append(chunk)

    report = "".join(report_chunks)

    # 5. Persist report to disk
    _REPORTS_DIR.mkdir(exist_ok=True)
    slug = _slugify(topic)
    report_path = _REPORTS_DIR / f"{slug}.md"
    report_path.write_text(report, encoding="utf-8")

    await emit("done",
               report_path=f"reports/{slug}.md",
               message=f"Report saved → reports/{slug}.md")
    return report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slugify(text: str) -> str:
    """Convert a topic string to a URL/filename-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:80]


def _normalize_title(title: str) -> str:
    return " ".join(title.lower().split())


def _deduplicate(papers: list[dict], seen: set[str], source: str) -> list[dict]:
    """Tag papers with their source and deduplicate by normalized title.

    Also ensures citation fields exist so score_papers can handle arXiv papers.
    """
    new: list[dict] = []
    for p in papers:
        norm = _normalize_title(p.get("title", ""))
        if not norm or norm in seen:
            continue
        seen.add(norm)
        p = dict(p)
        p["_source"] = source
        p.setdefault("citationCount", 0)
        p.setdefault("influentialCitationCount", 0)
        new.append(p)
    return new


async def _generate_queries(
    topic: str, provider: str, api_key: str, model: str
) -> list[str]:
    """Ask the LLM to generate 4 targeted search queries for the topic.

    Falls back to simple derived queries if the LLM call fails.
    """
    system = "You are a scientific literature search strategist."
    prompt = (
        f"Generate 4 distinct, targeted search queries to find the most important "
        f"academic papers about:\n\n{topic}\n\n"
        "Return ONLY a JSON array of 4 strings. No explanation, no markdown fences.\n"
        'Example: ["query one", "query two", "query three", "query four"]'
    )
    try:
        raw = await complete(
            provider, api_key, model, system,
            [{"role": "user", "content": prompt}],
            max_tokens=256,
        )
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if 0 <= start < end:
            queries = json.loads(raw[start:end])
            if isinstance(queries, list) and all(isinstance(q, str) for q in queries):
                return [q for q in queries[:4] if q.strip()]
    except Exception:
        pass
    # Fallback: derive minimal queries from the topic
    return [topic, f"{topic} review", f"{topic} survey", f"{topic} methods"]


async def _synthesize(
    topic: str,
    papers: list[dict],
    provider: str,
    api_key: str,
    model: str,
    emit: EmitFn,
):
    """Stream LLM synthesis of the research report.

    Async generator — yields text chunks and emits 'report_chunk' events.
    """
    paper_entries: list[str] = []
    for i, p in enumerate(papers, 1):
        title = p.get("title", "Untitled")

        raw_authors = p.get("authors") or []
        if isinstance(raw_authors, list):
            names = [
                a if isinstance(a, str) else a.get("name", "")
                for a in raw_authors[:3]
            ]
            author_str = ", ".join(n for n in names if n)
            if len(raw_authors) > 3:
                author_str += " et al."
        else:
            author_str = str(raw_authors)

        year = p.get("year") or (p.get("published", "")[:4] if p.get("published") else "n/a")
        cites = p.get("citationCount", "n/a")
        score = p.get("score", 0)
        abstract = (p.get("abstract") or "")[:400].strip()
        source = p.get("_source", "")

        paper_entries.append(
            f"[{i}] **{title}** — {author_str} ({year}) | "
            f"citations: {cites} | score: {score} | source: {source}\n"
            f"    {abstract}"
        )

    papers_block = "\n\n".join(paper_entries)
    today = datetime.date.today().isoformat()

    system = (
        "You are a Deep Researcher — a systematic scientific literature analyst. "
        "Write in precise, academic English. "
        "Cite every factual claim with inline (Author et al., Year) citations. "
        "Explicitly distinguish causal from correlational evidence. "
        "Never speculate beyond what the provided papers support."
    )

    user_message = (
        f'Analyze these {len(papers)} papers about "{topic}" and write a '
        f"comprehensive research report.\n\n"
        f"Papers (ranked by importance score, highest first):\n\n{papers_block}\n\n"
        "---\n\n"
        f"Write the report using this EXACT markdown structure:\n\n"
        f"# Deep Research Report: {topic}\n\n"
        f"**Date**: {today}\n"
        f"**Papers surveyed**: {len(papers)}\n"
        f"**Search strategy**: Multi-query search across arXiv and Semantic Scholar, "
        f"ranked by citation count (45%), influential citations (30%), recency (25%)\n\n"
        "---\n\n"
        "## 1. What Are Researchers Studying in This Field?\n\n"
        "## 2. What Data Do They Collect?\n\n"
        "## 3. How Do They Model It?\n\n"
        "## 4. What Do They Predict With That Data?\n\n"
        "## 5. Causation vs. Correlation\n\n"
        "## 6. Unexplored Areas\n\n"
        "---\n\n"
        "## References\n\n"
        "Use (Author et al., Year) for all inline citations. "
        "The References section must list every paper cited, alphabetically by first author."
    )

    async for chunk in stream_completion(
        provider, api_key, model,
        system=system,
        messages=[{"role": "user", "content": user_message}],
        max_tokens=8192,
    ):
        await emit("report_chunk", text=chunk)
        yield chunk
