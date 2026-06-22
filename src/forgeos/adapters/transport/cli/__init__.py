"""CLI transport — the primary, always-available interface."""

from __future__ import annotations

from forgeos.adapters.transport.cli.app import app, main

__all__ = ["app", "main"]
