#!/usr/bin/env python3
"""arXiv MCP server — stdio-based Model Context Protocol server for arXiv search.

Provides a `search_arxiv` tool that queries the arXiv API and returns
paper metadata: title, authors, abstract, arXiv ID, and PDF URL.

Usage:
    python arxiv_server.py  (started by VS Code via mcp.json)
"""

import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

ARXIV_API_URL = "http://export.arxiv.org/api/query"
ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"
MAX_RESULTS_LIMIT = 50


def search_arxiv(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Search arXiv and return paper metadata.

    Args:
        query: Search query string (supports arXiv query syntax).
        max_results: Maximum number of results to return (1-50).

    Returns:
        List of dicts with title, authors, abstract, arxiv_id, pdf_url,
        published, updated, categories.
    """
    max_results = max(1, min(max_results, MAX_RESULTS_LIMIT))
    params = urllib.parse.urlencode({
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    })
    url = f"{ARXIV_API_URL}?{params}"

    req = urllib.request.Request(url, headers={"User-Agent": "deep-research-agent/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        xml_data = response.read().decode("utf-8")

    root = ET.fromstring(xml_data)
    papers: list[dict[str, Any]] = []

    for entry in root.findall(f"{ATOM_NS}entry"):
        # arXiv ID from the <id> URL
        id_url = entry.findtext(f"{ATOM_NS}id", "")
        arxiv_id = id_url.split("/abs/")[-1] if "/abs/" in id_url else id_url

        title = entry.findtext(f"{ATOM_NS}title", "")
        title = " ".join(title.split())  # normalize whitespace

        abstract = entry.findtext(f"{ATOM_NS}summary", "")
        abstract = " ".join(abstract.split())

        authors = [
            author.findtext(f"{ATOM_NS}name", "")
            for author in entry.findall(f"{ATOM_NS}author")
        ]

        published = entry.findtext(f"{ATOM_NS}published", "")
        updated = entry.findtext(f"{ATOM_NS}updated", "")

        # PDF link
        pdf_url = ""
        for link in entry.findall(f"{ATOM_NS}link"):
            if link.get("title") == "pdf":
                pdf_url = link.get("href", "")
                break
        if not pdf_url and arxiv_id:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"

        categories = [
            cat.get("term", "")
            for cat in entry.findall(f"{ARXIV_NS}primary_category")
        ]
        categories += [
            cat.get("term", "")
            for cat in entry.findall(f"{ATOM_NS}category")
            if cat.get("term", "") not in categories
        ]

        papers.append({
            "arxiv_id": arxiv_id,
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "pdf_url": pdf_url,
            "published": published[:10] if published else "",
            "updated": updated[:10] if updated else "",
            "categories": categories,
        })

    return papers


# -- MCP stdio protocol --

TOOL_DEFINITION = {
    "name": "search_arxiv",
    "description": (
        "Search arXiv for scientific papers. Returns metadata including "
        "title, authors, abstract, arXiv ID, and PDF URL. Supports arXiv "
        "query syntax (e.g., 'ti:attention AND cat:cs.CL')."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query. Supports arXiv syntax: "
                "'ti:' (title), 'au:' (author), 'cat:' (category), "
                "'abs:' (abstract). Plain text searches all fields.",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of papers to return (1-50).",
                "default": 10,
                "minimum": 1,
                "maximum": 50,
            },
        },
        "required": ["query"],
    },
}


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
                    "name": "arxiv-search",
                    "version": "1.0.0",
                },
            },
        }

    if method == "notifications/initialized":
        return {}  # no response for notifications

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": [TOOL_DEFINITION]},
        }

    if method == "tools/call":
        tool_name = request.get("params", {}).get("name", "")
        arguments = request.get("params", {}).get("arguments", {})

        if tool_name != "search_arxiv":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "isError": True,
                    "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                },
            }

        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 10)

        if not query:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "isError": True,
                    "content": [{"type": "text", "text": "query parameter is required"}],
                },
            }

        try:
            papers = search_arxiv(query, max_results)
            result_text = json.dumps(papers, indent=2, ensure_ascii=False)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": result_text}],
                },
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "isError": True,
                    "content": [{"type": "text", "text": f"arXiv API error: {e}"}],
                },
            }

    # Unknown method
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
        if response:  # skip empty responses (notifications)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
