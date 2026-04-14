#!/usr/bin/env python3
"""Parse a scientific PDF and extract structured content as JSON.

Uses PyMuPDF (fitz) to extract text with multi-column layout handling.
Outputs JSON with title, abstract, sections, and references.

Usage:
    python parse_pdf.py <path_to_pdf>
"""

import json
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF


def extract_text_blocks(doc: fitz.Document) -> list[dict]:
    """Extract text blocks from all pages, sorted by reading order.

    Handles multi-column layouts by sorting blocks left-to-right within
    horizontal bands, then top-to-bottom.

    Args:
        doc: A PyMuPDF Document object.

    Returns:
        List of dicts with keys: text, page, bbox (x0, y0, x1, y1).
    """
    all_blocks: list[dict] = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("blocks")

        for block in blocks:
            x0, y0, x1, y1, text, block_no, block_type = block
            if block_type != 0:  # skip image blocks
                continue
            text = text.strip()
            if not text:
                continue
            all_blocks.append({
                "text": text,
                "page": page_num,
                "bbox": {"x0": x0, "y0": y0, "x1": x1, "y1": y1},
            })

    return all_blocks


def sort_blocks_reading_order(
    blocks: list[dict], band_tolerance: float = 15.0
) -> list[dict]:
    """Sort text blocks into reading order for multi-column layouts.

    Groups blocks into horizontal bands (rows), sorts left-to-right
    within each band, then orders bands top-to-bottom.

    Args:
        blocks: List of block dicts with bbox info.
        band_tolerance: Vertical distance (pts) to consider blocks on the
            same line.

    Returns:
        Blocks sorted in reading order.
    """
    if not blocks:
        return blocks

    sorted_by_y = sorted(blocks, key=lambda b: b["bbox"]["y0"])
    bands: list[list[dict]] = []
    current_band: list[dict] = [sorted_by_y[0]]

    for block in sorted_by_y[1:]:
        if abs(block["bbox"]["y0"] - current_band[0]["bbox"]["y0"]) <= band_tolerance:
            current_band.append(block)
        else:
            bands.append(current_band)
            current_band = [block]
    bands.append(current_band)

    ordered: list[dict] = []
    for band in bands:
        band.sort(key=lambda b: b["bbox"]["x0"])
        ordered.extend(band)

    return ordered


def extract_full_text(doc: fitz.Document) -> str:
    """Extract full text from a PDF in reading order.

    Args:
        doc: A PyMuPDF Document object.

    Returns:
        Full text of the document as a single string.
    """
    pages_text: list[str] = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("blocks")
        page_blocks: list[dict] = []

        for block in blocks:
            x0, y0, x1, y1, text, block_no, block_type = block
            if block_type != 0:
                continue
            text = text.strip()
            if not text:
                continue
            page_blocks.append({
                "text": text,
                "page": page_num,
                "bbox": {"x0": x0, "y0": y0, "x1": x1, "y1": y1},
            })

        ordered = sort_blocks_reading_order(page_blocks)
        page_text = "\n".join(b["text"] for b in ordered)
        pages_text.append(page_text)

    return "\n\n".join(pages_text)


def extract_title(text: str, doc: fitz.Document) -> str:
    """Extract the paper title from the first page.

    Uses font size heuristics: the largest text on page 1 is likely the title.

    Args:
        text: Full extracted text (fallback).
        doc: A PyMuPDF Document object.

    Returns:
        Extracted title string.
    """
    if len(doc) == 0:
        return ""

    page = doc[0]
    blocks = page.get_text("dict")["blocks"]
    max_size = 0.0
    title_spans: list[tuple[float, float, str]] = []

    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                size = span["size"]
                span_text = span["text"].strip()
                if not span_text:
                    continue
                if size > max_size:
                    max_size = size
                    title_spans = [(line["bbox"][1], size, span_text)]
                elif abs(size - max_size) < 0.5:
                    title_spans.append((line["bbox"][1], size, span_text))

    if title_spans:
        title_spans.sort(key=lambda s: s[0])
        title = " ".join(s[2] for s in title_spans)
        title = re.sub(r"\s+", " ", title).strip()
        return title

    # Fallback: first non-empty line
    for line in text.split("\n"):
        line = line.strip()
        if line and len(line) > 5:
            return line
    return ""


_ABSTRACT_PATTERN = re.compile(
    r"(?:^|\n)\s*Abstract\s*[\n:.—–-]\s*(.*?)(?=\n\s*(?:1[\s.]|Introduction|Keywords|I\.\s))",
    re.IGNORECASE | re.DOTALL,
)


def extract_abstract(text: str) -> str:
    """Extract the abstract from paper text.

    Args:
        text: Full extracted text.

    Returns:
        Abstract text, or empty string if not found.
    """
    match = _ABSTRACT_PATTERN.search(text)
    if match:
        abstract = match.group(1).strip()
        abstract = re.sub(r"\s+", " ", abstract)
        return abstract
    return ""


_SECTION_PATTERN = re.compile(
    r"(?:^|\n)\s*(\d+\.?\s+[A-Z][^\n]{2,80}|[IVX]+\.?\s+[A-Z][^\n]{2,80})\s*\n",
)


def extract_sections(text: str) -> list[dict]:
    """Extract sections with their headings and content.

    Args:
        text: Full extracted text.

    Returns:
        List of dicts with 'heading' and 'content' keys.
    """
    matches = list(_SECTION_PATTERN.finditer(text))
    if not matches:
        return [{"heading": "Full Text", "content": text}]

    sections: list[dict] = []
    for i, match in enumerate(matches):
        heading = re.sub(r"\s+", " ", match.group(1)).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        sections.append({"heading": heading, "content": content})

    return sections


_REFERENCES_PATTERN = re.compile(
    r"(?:^|\n)\s*(?:References|Bibliography|Works Cited)\s*\n",
    re.IGNORECASE,
)


def extract_references_section(text: str) -> str:
    """Extract the raw references section text.

    Args:
        text: Full extracted text.

    Returns:
        References section text, or empty string if not found.
    """
    match = _REFERENCES_PATTERN.search(text)
    if match:
        return text[match.end():].strip()
    return ""


def parse_references(references_text: str) -> list[str]:
    """Split references section into individual reference strings.

    Args:
        references_text: Raw text of the references section.

    Returns:
        List of individual reference strings.
    """
    if not references_text:
        return []

    # Try numbered references: [1], [2], ... or 1. 2. ...
    numbered = re.split(r"\n\s*\[?\d+\]?[\s.)]+", references_text)
    numbered = [ref.strip() for ref in numbered if ref.strip()]
    if len(numbered) > 2:
        return numbered

    # Fall back to splitting on blank lines or author-year patterns
    by_line = re.split(r"\n{2,}", references_text)
    by_line = [ref.strip() for ref in by_line if ref.strip()]
    if len(by_line) > 2:
        return by_line

    # Last resort: split on lines starting with uppercase
    entries = re.split(r"\n(?=[A-Z])", references_text)
    return [e.strip() for e in entries if e.strip()]


def parse_pdf(pdf_path: str) -> dict:
    """Parse a PDF and return structured content.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Dict with keys: title, abstract, full_text, sections, references,
        page_count, file_path.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if not path.suffix.lower() == ".pdf":
        raise ValueError(f"Not a PDF file: {pdf_path}")

    doc = fitz.open(str(path))
    full_text = extract_full_text(doc)
    title = extract_title(full_text, doc)
    abstract = extract_abstract(full_text)
    sections = extract_sections(full_text)
    references_text = extract_references_section(full_text)
    references = parse_references(references_text)

    result = {
        "title": title,
        "abstract": abstract,
        "full_text": full_text,
        "sections": sections,
        "references": references,
        "page_count": len(doc),
        "file_path": str(path.resolve()),
    }

    doc.close()
    return result


def main() -> None:
    """Entry point: parse a PDF and print structured JSON to stdout."""
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <pdf_path>", file=sys.stderr)
        sys.exit(1)

    pdf_path = sys.argv[1]
    try:
        result = parse_pdf(pdf_path)
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    except (FileNotFoundError, ValueError) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
