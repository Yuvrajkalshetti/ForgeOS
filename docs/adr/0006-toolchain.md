# ADR 0006: Toolchain — Python 3.12, uv, ruff, mypy (strict), pytest

- **Status:** accepted
- **Date:** 2026-06-20

## Context
Need a fast, modern, reproducible Python toolchain with strong typing.

## Decision
Python 3.12; uv for env/deps; ruff for lint+format; mypy strict on `src/`;
pytest for tests. CI runs all four.

## Consequences
- Consistent local + CI gates.
- In constrained environments without ruff/mypy, `scripts/check.py` provides a
  stdlib-only substitute (syntax + annotation + import hygiene); it does not
  replace ruff/mypy and is clearly labelled as a fallback.
