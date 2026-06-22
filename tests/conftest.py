"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """A temporary project root with an empty ``.forgeos`` directory."""
    (tmp_path / ".forgeos").mkdir()
    return tmp_path
