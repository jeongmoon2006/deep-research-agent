#!/usr/bin/env python3
"""Extract citations and references from scientific paper text.

Takes extracted paper text (from parse_pdf.py JSON output or raw text)
and identifies inline citations in (Author, Year) format, then parses
the references section into structured entries.

Usage:
    python extract_citations.py <json_or_text_file>
    python parse_pdf.py paper.pdf | python extract_citations.py -
"""

import json
import re
import sys
from pathlib import Path


_INLINE_CITATION_PATTERN = re.compile(
    r"\(("
    r"(?:[A-Z][a-z]+(?:\s+(?:and|&)\s+[A-Z][a-z]+)*"
    r"(?:\s+et\s+al\.?)?"
    r",?\s*\d{4}"
    r"(?:\s*;\s*"
    r"[A-Z][a-z]+(?:\s+(?:and|&)\s+[A-Z][a-z]+)*"
    r"(?:\s+et\s+al\.?)?"
    r",?\s*\d{4})*"
    r")"
    r"\)",
)

_SINGLE_CITE_PATTERN = re.compile(
    r"([A-Z][a-z]+(?:\s+(?:and|&)\s+[A-Z][a-z]+)*(?:\s+et\s+al\.?)?)"
    r",?\s*(\d{4})"
)


def extract_inline_citations(text: str) -> list[dict]:
    """Extract inline citations in (Author, Year) format from text.

    Handles single citations like (Smith, 2020), multi-author
    (Smith and Jones, 2020), et al. (Smith et al., 2020), and
    compound citations (Smith, 2020; Jones, 2021).

    Args:
        text: Full paper text.

    Returns:
        List of dicts with 'authors' and 'year' keys, deduplicated.
    """
    citations: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for match in _INLINE_CITATION_PATTERN.finditer(text):
        group = match.group(1)
        for cite_match in _SINGLE_CITE_PATTERN.finditer(group):
            authors = cite_match.group(1).strip()
            year = cite_match.group(2).strip()
            key = (authors, year)
            if key not in seen:
                seen.add(key)
                citations.append({"authors": authors, "year": year})

    return citations


_REFERENCES_PATTERN = re.compile(
    r"(?:^|\n)\s*(?:References|Bibliography|Works Cited)\s*\n",
    re.IGNORECASE,
)


def extract_references_text(text: str) -> str:
    """Extract the raw references section from paper text.

    Args:
        text: Full paper text.

    Returns:
        References section text, or empty string if not found.
    """
    match = _REFERENCES_PATTERN.search(text)
    if match:
        return text[match.end():].strip()
    return ""


def split_references(references_text: str) -> list[str]:
    """Split a references section into individual reference strings.

    Args:
        references_text: Raw text of the references section.

    Returns:
        List of individual reference strings.
    """
    if not references_text:
        return []

    # Numbered: [1] or 1.
    numbered = re.split(r"\n\s*\[?\d+\]?[\s.)]+", references_text)
    numbered = [r.strip() for r in numbered if r.strip()]
    if len(numbered) > 2:
        return numbered

    # Blank-line separated
    by_blank = re.split(r"\n{2,}", references_text)
    by_blank = [r.strip() for r in by_blank if r.strip()]
    if len(by_blank) > 2:
        return by_blank

    # Lines starting with uppercase (author names)
    by_author = re.split(r"\n(?=[A-Z])", references_text)
    return [r.strip() for r in by_author if r.strip()]


_YEAR_PATTERN = re.compile(r"\b((?:19|20)\d{2})\b")
_AUTHOR_YEAR_PATTERN = re.compile(
    r"^(.+?)\s*[(\[]?\s*((?:19|20)\d{2})\s*[)\]]?"
)
_TITLE_PATTERN = re.compile(
    r"(?:19|20)\d{2}\s*[)\.]?\s*[.]?\s*(.+?)\s*[.]"
)
_JOURNAL_PATTERN = re.compile(
    r"(?:In\s+)?([A-Z][^.]+(?:Journal|Review|Proceedings|Conference|Trans\.|"
    r"Letters|Bulletin|Annals|Archives|Quarterly|Monthly|Science|Nature|"
    r"PNAS|PLoS|BMJ|JAMA|Lancet|Cell|Neuron|ICML|NeurIPS|ICLR|ACL|"
    r"EMNLP|CVPR|ICCV|ECCV|IEEE|ACM)[^.]*)",
    re.IGNORECASE,
)


def parse_reference(ref_text: str) -> dict:
    """Parse a single reference string into structured fields.

    Args:
        ref_text: A single reference entry.

    Returns:
        Dict with 'raw', 'authors', 'year', 'title', 'journal' keys.
    """
    result: dict = {
        "raw": ref_text,
        "authors": "",
        "year": "",
        "title": "",
        "journal": "",
    }

    # Year
    year_match = _YEAR_PATTERN.search(ref_text)
    if year_match:
        result["year"] = year_match.group(1)

    # Authors (text before the year)
    author_match = _AUTHOR_YEAR_PATTERN.match(ref_text)
    if author_match:
        authors = author_match.group(1).strip().rstrip(",").rstrip(".")
        result["authors"] = authors

    # Title (text after year, before first period)
    title_match = _TITLE_PATTERN.search(ref_text)
    if title_match:
        title = title_match.group(1).strip().strip('"').strip("'")
        result["title"] = title

    # Journal
    journal_match = _JOURNAL_PATTERN.search(ref_text)
    if journal_match:
        result["journal"] = journal_match.group(1).strip().rstrip(".")

    return result


def extract_citations(text: str) -> dict:
    """Extract all citation data from paper text.

    Args:
        text: Full paper text (or JSON with 'full_text' key).

    Returns:
        Dict with 'inline_citations', 'references', and 'citation_count'.
    """
    inline = extract_inline_citations(text)
    ref_text = extract_references_text(text)
    raw_refs = split_references(ref_text)
    parsed_refs = [parse_reference(r) for r in raw_refs]

    return {
        "inline_citations": inline,
        "references": parsed_refs,
        "citation_count": len(inline),
        "reference_count": len(parsed_refs),
    }


def load_input(input_path: str) -> str:
    """Load input text from a file or stdin.

    Accepts either raw text or JSON output from parse_pdf.py
    (uses the 'full_text' field).

    Args:
        input_path: File path, or '-' for stdin.

    Returns:
        Paper text as a string.
    """
    if input_path == "-":
        raw = sys.stdin.read()
    else:
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        raw = path.read_text(encoding="utf-8")

    # Try parsing as JSON (output of parse_pdf.py)
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "full_text" in data:
            return data["full_text"]
    except (json.JSONDecodeError, TypeError):
        pass

    return raw


def main() -> None:
    """Entry point: extract citations and print JSON to stdout."""
    if len(sys.argv) != 2:
        print(
            f"Usage: {sys.argv[0]} <json_or_text_file>\n"
            f"       {sys.argv[0]} -  (read from stdin)",
            file=sys.stderr,
        )
        sys.exit(1)

    input_path = sys.argv[1]
    try:
        text = load_input(input_path)
        result = extract_citations(text)
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
