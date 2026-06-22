from __future__ import annotations

from forgeos.core.repo_intel.deps import extract_imports, is_stdlib


def test_python_imports_top_level() -> None:
    source = "import json\nfrom pkg_b.helper import normalize\nimport os.path\n"
    assert extract_imports("python", source) == ["json", "os", "pkg_b"]


def test_python_ignores_relative_imports() -> None:
    source = "from . import sibling\nfrom ..pkg import thing\n"
    assert extract_imports("python", source) == []


def test_python_syntax_error_yields_empty() -> None:
    assert extract_imports("python", "def (oops\n") == []


def test_is_stdlib() -> None:
    assert is_stdlib("json")
    assert is_stdlib("os")
    assert not is_stdlib("httpx")


def test_js_imports() -> None:
    source = (
        "import React from 'react';\n"
        "import { x } from './local';\n"
        "const fs = require('node:fs');\n"
    )
    assert extract_imports("javascript", source) == ["./local", "node:fs", "react"]


def test_unknown_language_yields_empty() -> None:
    assert extract_imports(None, "anything") == []
