"""Lexicographically sortable, time-prefixed identifiers (ULID-style).

ForgeOS avoids a third-party ULID dependency; this stdlib implementation produces
26-character Crockford base32 strings whose leading bits encode the millisecond
timestamp, so IDs sort chronologically. ``new_id`` prefixes them per entity type
(e.g. ``mem_...``, ``card_...``) to keep references self-describing.
"""

from __future__ import annotations

import os
import time

# Crockford base32 alphabet (excludes I, L, O, U to avoid ambiguity).
_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_ENCODED_LEN = 26


def ulid(timestamp_ms: int | None = None) -> str:
    """Return a 26-char ULID-style id. Monotonic by millisecond timestamp."""
    if timestamp_ms is None:
        timestamp_ms = time.time_ns() // 1_000_000
    randomness = int.from_bytes(os.urandom(10), "big")  # 80 random bits
    value = (timestamp_ms << 80) | randomness  # 128-bit value
    chars = [""] * _ENCODED_LEN
    for i in range(_ENCODED_LEN - 1, -1, -1):
        chars[i] = _CROCKFORD[value & 0x1F]
        value >>= 5
    return "".join(chars)


def new_id(prefix: str, timestamp_ms: int | None = None) -> str:
    """Return a prefixed id such as ``mem_01J9...``. Prefix must be non-empty."""
    if not prefix:
        raise ValueError("prefix must be a non-empty string")
    return f"{prefix}_{ulid(timestamp_ms)}"
