#!/usr/bin/env python3
"""Semantic Scholar MCP server — stdio-based Model Context Protocol server.

Provides two tools:
- `search_semantic_scholar`: Query the Semantic Scholar API for papers,
  returning metadata including citation counts for paper scoring.
- `score_papers`: Compute a numeric relevance score for a list of papers
  using citation count, influential citation count, and recency.

Usage:
    python semantic_scholar_server.py  (started by VS Code via mcp.json)

Environment variables:
    SEMANTIC_SCHOLAR_API_KEY — optional API key for higher rate limits
        (without key: 1 req/s; with key: up to 10 req/s)
"""

import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
from typing import Any

SS_API_BASE = "https://api.semanticscholar.org/graph/v1"
_PAPER_FIELDS = (
    "title,authors,abstract,year,citationCount,influentialCitationCount,"
    "venue,openAccessPdf,externalIds,publicationTypes"
)
MAX_RESULTS_LIMIT = 100
_CURRENT_YEAR = 2026

# Simple in-memory rate limiter: track last request time
_last_request_time: float = 0.0


def _get_headers() -> dict[str, str]:
    """Build request headers, including API key if set.

    Returns:
        Dict of HTTP headers.
    """
    headers = {"User-Agent": "deep-research-agent/1.0"}
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "")
    if api_key:
        headers["x-api-key"] = api_key
    return headers


def _rate_limited_request(url: str) -> bytes:
    """Perform an HTTP GET with rate limiting (1 req/s without API key).

    Args:
        url: Full URL to fetch.

    Returns:
        Raw response bytes.
    """
    global _last_request_time
    has_key = bool(os.environ.get("SEMANTIC_SCHOLAR_API_KEY", ""))
    min_interval = 0.11 if has_key else 1.05  # seconds between requests

    elapsed = time.monotonic() - _last_request_time
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)

    req = urllib.request.Request(url, headers=_get_headers())
    with urllib.request.urlopen(req, timeout=30) as response:
        data = response.read()

    _last_request_time = time.monotonic()
    return data


def search_semantic_scholar(
    query: str, limit: int = 20, fields_of_study: str = ""
) -> list[dict[str, Any]]:
    """Search Semantic Scholar and return paper metadata with citation counts.

    Args:
        query: Free-text search query.
        limit: Maximum number of results to return (1-100).
        fields_of_study: Optional comma-separated field filter, e.g.
            'Computer Science,Biology'. Empty string means no filter.

    Returns:
        List of paper dicts with keys: paperId, title, authors, abstract,
        year, citationCount, influentialCitationCount, venue,
        openAccessPdfUrl, arxivId, doi, publicationTypes.
    """
    limit = max(1, min(limit, MAX_RESULTS_LIMIT))
    params: dict[str, Any] = {
        "query": query,
        "fields": _PAPER_FIELDS,
        "limit": limit,
    }
    if fields_of_study:
        params["fieldsOfStudy"] = fields_of_study

    url = f"{SS_API_BASE}/paper/search?{urllib.parse.urlencode(params)}"
    raw = _rate_limited_request(url)
    data = json.loads(raw)

    papers: list[dict[str, Any]] = []
    for item in data.get("data", []):
        external_ids = item.get("externalIds") or {}
        pdf_info = item.get("openAccessPdf") or {}
        authors = [
            a.get("name", "") for a in (item.get("authors") or [])
        ]
        papers.append({
            "paperId": item.get("paperId", ""),
            "title": item.get("title", ""),
            "authors": authors,
            "abstract": item.get("abstract") or "",
            "year": item.get("year"),
            "citationCount": item.get("citationCount") or 0,
            "influentialCitationCount": item.get("influentialCitationCount") or 0,
            "venue": item.get("venue") or "",
            "openAccessPdfUrl": pdf_info.get("url", ""),
            "arxivId": external_ids.get("ArXiv", ""),
            "doi": external_ids.get("DOI", ""),
            "publicationTypes": item.get("publicationTypes") or [],
        })

    return papers


def score_papers(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Score and rank a list of papers by importance.

    Scoring formula (all components normalized to [0, 1]):
      score = 0.45 * log_citation_score
            + 0.30 * influential_citation_score
            + 0.25 * recency_score

    log_citation_score:
        log1p(citationCount) normalized by the max in the batch.
    influential_citation_score:
        log1p(influentialCitationCount) normalized by the max in the batch.
    recency_score:
        Papers from the current year score 1.0; score decays linearly to
        0.0 at 20 years ago. Papers with no year score 0.0.

    Args:
        papers: List of paper dicts. Must have at minimum: 'citationCount',
            'influentialCitationCount', and 'year' keys.

    Returns:
        Same list sorted descending by 'score', with 'score' added to
        each dict (rounded to 4 decimal places).
    """
    if not papers:
        return []

    log_cites = [math.log1p(p.get("citationCount") or 0) for p in papers]
    log_inf = [math.log1p(p.get("influentialCitationCount") or 0) for p in papers]

    max_log_cites = max(log_cites) if max(log_cites) > 0 else 1.0
    max_log_inf = max(log_inf) if max(log_inf) > 0 else 1.0

    scored: list[dict[str, Any]] = []
    for paper, lc, li in zip(papers, log_cites, log_inf):
        year = paper.get("year")
        if year:
            age = max(0, _CURRENT_YEAR - year)
            recency = max(0.0, 1.0 - age / 20.0)
        else:
            recency = 0.0

        score = (
            0.45 * (lc / max_log_cites)
            + 0.30 * (li / max_log_inf)
            + 0.25 * recency
        )
        scored.append({**paper, "score": round(score, 4)})

    scored.sort(key=lambda p: p["score"], reverse=True)
    return scored


# -- MCP stdio protocol --

TOOL_DEFINITIONS = [
    {
        "name": "search_semantic_scholar",
        "description": (
            "Search Semantic Scholar for scientific papers. Returns metadata "
            "including title, authors, abstract, citation count, influential "
            "citation count, year, venue, and open-access PDF URL. Use this "
            "to find papers and retrieve citation data for scoring."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Free-text search query.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of papers to return (1-100).",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100,
                },
                "fields_of_study": {
                    "type": "string",
                    "description": (
                        "Optional comma-separated field filter, e.g. "
                        "'Computer Science' or 'Biology,Medicine'. "
                        "Leave empty to search all fields."
                    ),
                    "default": "",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "score_papers",
        "description": (
            "Score and rank a list of papers by importance using citation "
            "count, influential citation count, and recency. Returns the "
            "same list sorted descending by 'score' (0–1). Use after "
            "search_semantic_scholar to prioritize which papers to read."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "papers": {
                    "type": "array",
                    "description": (
                        "List of paper objects, each with at minimum "
                        "'citationCount', 'influentialCitationCount', and "
                        "'year' fields. Typically the output of "
                        "search_semantic_scholar."
                    ),
                    "items": {"type": "object"},
                },
            },
            "required": ["papers"],
        },
    },
]


def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    """Handle a single JSON-RPC request.

    Args:
        request: Parsed JSON-RPC request dict.

    Returns:
        JSON-RPC response dict.
    """
    method = request.get("method", "")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {
                    "name": "semantic-scholar",
                    "version": "1.0.0",
                },
            },
        }

    if method == "notifications/initialized":
        return {}

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOL_DEFINITIONS},
        }

    if method == "tools/call":
        tool_name = request.get("params", {}).get("name", "")
        arguments = request.get("params", {}).get("arguments", {})

        if tool_name == "search_semantic_scholar":
            query = arguments.get("query", "")
            if not query:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "isError": True,
                        "content": [{"type": "text", "text": "query is required"}],
                    },
                }
            try:
                papers = search_semantic_scholar(
                    query=query,
                    limit=arguments.get("limit", 20),
                    fields_of_study=arguments.get("fields_of_study", ""),
                )
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(papers, indent=2, ensure_ascii=False),
                            }
                        ]
                    },
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "isError": True,
                        "content": [
                            {"type": "text", "text": f"Semantic Scholar API error: {e}"}
                        ],
                    },
                }

        if tool_name == "score_papers":
            papers = arguments.get("papers", [])
            if not isinstance(papers, list):
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "isError": True,
                        "content": [{"type": "text", "text": "papers must be a list"}],
                    },
                }
            try:
                scored = score_papers(papers)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(scored, indent=2, ensure_ascii=False),
                            }
                        ]
                    },
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "isError": True,
                        "content": [{"type": "text", "text": f"Scoring error: {e}"}],
                    },
                }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "isError": True,
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
            },
        }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def main() -> None:
    """Run the MCP server, reading JSON-RPC from stdin and writing to stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        response = handle_request(request)
        if response:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
