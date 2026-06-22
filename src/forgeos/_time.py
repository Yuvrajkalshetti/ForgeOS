"""Shared time helpers."""

from __future__ import annotations

import datetime


def utcnow() -> datetime.datetime:
    """Timezone-aware current UTC time (the default clock across engines)."""
    return datetime.datetime.now(datetime.UTC)
