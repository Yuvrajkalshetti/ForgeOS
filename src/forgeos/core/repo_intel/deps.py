"""Dependency discovery: Python (AST, first-class) and JS/TS (regex, heuristic).

Returns the top-level import specifiers per file. Classification into
internal/external/stdlib happens in the engine, which knows the module set.
All static — no execution of the analyzed code, no provider calls.
"""

from __future__ import annotations

import ast
import re
import sys

_STDLIB: frozenset[str] = frozenset(sys.stdlib_module_names)

# `import x from 'spec'`, `import 'spec'`, `export ... from 'spec'`, `require('spec')`
_JS_IMPORT_RE = re.compile(
    r"""(?:\bfrom\s+|\bimport\s+|\brequire\s*\(\s*)['"]([^'"]+)['"]""",
)


def is_stdlib(top_level: str) -> bool:
    """True if ``top_level`` is a Python standard-library module."""
    return top_level in _STDLIB


def _python_imports(source: str) -> set[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def _js_imports(source: str) -> set[str]:
    return {match.split("/")[0] if not match.startswith(".") else match
            for match in _JS_IMPORT_RE.findall(source)}


def extract_imports(language: str | None, source: str) -> list[str]:
    """Return sorted, unique top-level import specifiers for a source file."""
    if language == "python":
        return sorted(_python_imports(source))
    if language in ("javascript", "typescript"):
        return sorted(_js_imports(source))
    return []
