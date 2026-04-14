#!/usr/bin/env python3
"""Validate deep research agent report output after tool use.

Reads PostToolUse hook input from stdin. If the tool output contains
a research report, validates that all 6 required sections are present,
each claim has a citation, no section is empty, and causal vs.
correlational distinctions are explicitly stated.

Returns JSON to stdout with a systemMessage containing missing items
so the agent can fix them.
"""

import json
import re
import sys

REQUIRED_SECTIONS = [
    {
        "id": "field_overview",
        "heading_pattern": r"##\s*1\.\s*What\s+Are\s+Researchers\s+Studying",
        "label": "Section 1: What Are Researchers Studying in This Field?",
    },
    {
        "id": "data",
        "heading_pattern": r"##\s*2\.\s*What\s+Data\s+Do\s+They\s+Collect",
        "label": "Section 2: What Data Do They Collect?",
    },
    {
        "id": "modeling",
        "heading_pattern": r"##\s*3\.\s*How\s+Do\s+They\s+Model",
        "label": "Section 3: How Do They Model It?",
    },
    {
        "id": "predictions",
        "heading_pattern": r"##\s*4\.\s*What\s+Do\s+They\s+Predict",
        "label": "Section 4: What Do They Predict With That Data?",
    },
    {
        "id": "causal_evaluation",
        "heading_pattern": r"##\s*5\.\s*Causation\s+vs\.?\s+Correlation",
        "label": "Section 5: Causation vs. Correlation",
    },
    {
        "id": "unexplored",
        "heading_pattern": r"##\s*6\.\s*Unexplored\s+Areas",
        "label": "Section 6: Unexplored Areas",
    },
]

REPORT_MARKER = re.compile(r"#\s*Deep\s+Research\s+Report", re.IGNORECASE)

CITATION_PATTERN = re.compile(
    r"\([A-Z][a-z]+(?:\s+(?:and|&)\s+[A-Z][a-z]+)*(?:\s+et\s+al\.?)?,?\s*\d{4}\)"
)

CAUSAL_KEYWORDS = re.compile(
    r"\b(causal|correlational|correlation|observational|RCT|"
    r"randomized|intervention|mixed evidence)\b",
    re.IGNORECASE,
)


def extract_section_content(text: str, section: dict, all_sections: list[dict]) -> str:
    """Extract the content of a section between its heading and the next heading.

    Args:
        text: Full report text.
        section: The section dict to extract.
        all_sections: All section dicts for boundary detection.

    Returns:
        Section content string, or empty string if heading not found.
    """
    match = re.search(section["heading_pattern"], text, re.IGNORECASE)
    if not match:
        return ""

    start = match.end()

    # Find the next section heading or end of text
    next_start = len(text)
    for other in all_sections:
        if other["id"] == section["id"]:
            continue
        other_match = re.search(other["heading_pattern"], text, re.IGNORECASE)
        if other_match and other_match.start() > match.start():
            next_start = min(next_start, other_match.start())

    # Also check for References section
    ref_match = re.search(r"##\s*References", text, re.IGNORECASE)
    if ref_match and ref_match.start() > match.start():
        next_start = min(next_start, ref_match.start())

    return text[start:next_start].strip()


def validate_report(text: str) -> list[str]:
    """Validate a research report against all quality checks.

    Args:
        text: The report text to validate.

    Returns:
        List of validation failure messages. Empty list means all checks pass.
    """
    failures: list[str] = []

    # Check 1: All 6 sections present
    missing_sections: list[str] = []
    for section in REQUIRED_SECTIONS:
        if not re.search(section["heading_pattern"], text, re.IGNORECASE):
            missing_sections.append(section["label"])

    if missing_sections:
        failures.append(
            "Missing required sections:\n- " + "\n- ".join(missing_sections)
        )

    # Check 2: No section is empty
    empty_sections: list[str] = []
    for section in REQUIRED_SECTIONS:
        content = extract_section_content(text, section, REQUIRED_SECTIONS)
        if not content or len(content.strip()) < 20:
            if section["label"] not in missing_sections:
                empty_sections.append(section["label"])

    if empty_sections:
        failures.append(
            "Empty or near-empty sections:\n- " + "\n- ".join(empty_sections)
        )

    # Check 3: Claims have citations
    uncited_sections: list[str] = []
    for section in REQUIRED_SECTIONS:
        content = extract_section_content(text, section, REQUIRED_SECTIONS)
        if not content:
            continue
        # Split into sentences and check for at least some citations
        sentences = re.split(r"[.!?]\s+", content)
        claim_sentences = [
            s for s in sentences
            if len(s) > 40 and not s.strip().startswith(("#", "-", "|", "*"))
        ]
        if claim_sentences:
            cited = sum(1 for s in claim_sentences if CITATION_PATTERN.search(s))
            ratio = cited / len(claim_sentences) if claim_sentences else 0
            if ratio < 0.3:
                uncited_sections.append(
                    f"{section['label']} — only {cited}/{len(claim_sentences)} "
                    f"claim sentences have citations"
                )

    if uncited_sections:
        failures.append(
            "Sections with insufficient citations:\n- "
            + "\n- ".join(uncited_sections)
        )

    # Check 4: Causal vs correlational distinction in section 5
    causal_content = extract_section_content(
        text,
        REQUIRED_SECTIONS[4],  # causal_evaluation section
        REQUIRED_SECTIONS,
    )
    if causal_content and not CAUSAL_KEYWORDS.search(causal_content):
        failures.append(
            "Section 5 (Causation vs. Correlation) does not explicitly use "
            "causal/correlational classification language. Each major finding "
            "must be labeled as Causal, Correlational, or Mixed."
        )

    return failures


def main() -> None:
    """Read PostToolUse hook input from stdin, validate, write JSON to stdout."""
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # No valid input — nothing to validate
        json.dump({"continue": True}, sys.stdout)
        return

    # Extract tool output text from the hook input
    tool_output = ""
    tool_result = hook_input.get("toolResult", {})
    if isinstance(tool_result, dict):
        content = tool_result.get("content", "")
        if isinstance(content, str):
            tool_output = content
        elif isinstance(content, list):
            tool_output = "\n".join(
                item.get("text", "") for item in content if isinstance(item, dict)
            )

    # Only validate if the output looks like a research report
    if not tool_output or not REPORT_MARKER.search(tool_output):
        json.dump({"continue": True}, sys.stdout)
        return

    failures = validate_report(tool_output)

    if not failures:
        json.dump({"continue": True}, sys.stdout)
    else:
        feedback = (
            "REPORT VALIDATION FAILED — fix the following issues before "
            "finalizing:\n\n" + "\n\n".join(failures)
        )
        json.dump(
            {
                "continue": True,
                "systemMessage": feedback,
            },
            sys.stdout,
        )

    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
