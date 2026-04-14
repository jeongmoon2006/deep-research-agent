# Project Guidelines

## Overview

Deep Research Agent — a VS Code Agents API project that surveys scientific literature and produces structured research reports. Python 3.11+.

## Code Style

- Python with type hints on all function signatures (parameters and return types)
- Google-style docstrings on all public functions and classes
- Format with the project's configured formatter before committing

## Architecture

- `.github/agents/` — Custom agent definitions (`.agent.md`)
- `.github/skills/paper-analysis/` — Deterministic Python scripts for PDF parsing and citation extraction
- `tools/` — MCP server scripts (e.g., `arxiv_server.py`)
- `reports/` — Generated research reports (auto-created by the deep-researcher agent)
- MCP servers: `arxiv` (arXiv API via `tools/arxiv_server.py`), `semantic-scholar` (Semantic Scholar API)

## Build and Test

```bash
pip install -r requirements.txt    # Install dependencies
pytest                             # Run all tests
pytest tests/ -v                   # Verbose test output
```

## Conventions

- **No API keys in code**: Use environment variables or `.env` files (`.env` is gitignored). Never hardcode secrets.
- **Testing**: Use `pytest`. Every module with logic gets a corresponding `tests/test_<module>.py`.
- **Dependencies**: Managed via `pip` and `requirements.txt`. Pin versions.
- **MCP tools**: arXiv and Semantic Scholar integrations are accessed through MCP servers, not direct HTTP calls in application code.
- **Paper analysis scripts**: The `paper-analysis` skill contains deterministic scripts — do not add LLM calls or non-deterministic behavior to those scripts.
