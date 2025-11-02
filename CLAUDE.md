# CLAUDE.md

This repository hosts `sync-ai-coding-instructions`, a Python CLI tool that
keeps three markdown files—`AGENTS.md`, `CLAUDE.md`, and
`GEMINI.md`—synchronized. The tool copies the body of the most recently updated
file to the others while preserving each file’s header line and exits with
status codes that describe what happened (no files, files created, or files
updated).

## 1. Project Layout

- `pyproject.toml` – project metadata, CLI entry point, pytest config.
- `sync_ai_coding_instructions/` – package containing the main CLI logic.
- `tests/` – pytest suite covering synchronization behaviour and CLI parsing.
- `.pre-commit-config.yaml` – runs the synchronizer as a pre-commit hook.
- `README.md` – instructions and high-level overview.

Install dependencies, run `pytest` to execute the test suite, and use
`python -m sync_ai_coding_instructions.main` (or the
`sync-ai-coding-instructions` console script once installed) to synchronize the
markdown files. Pass a custom comma-separated list through `--files` when you
need to keep additional instruction files in sync.
