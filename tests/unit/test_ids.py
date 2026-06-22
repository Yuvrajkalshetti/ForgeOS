from __future__ import annotations

import pytest

from forgeos._ids import new_id, ulid


def test_ulid_length_and_alphabet() -> None:
    value = ulid()
    assert len(value) == 26
    assert set(value) <= set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")


def test_ulid_is_time_sortable() -> None:
    earlier = ulid(timestamp_ms=1_000)
    later = ulid(timestamp_ms=2_000)
    assert earlier < later


def test_ulids_are_unique() -> None:
    values = {ulid() for _ in range(1000)}
    assert len(values) == 1000


def test_new_id_prefixes() -> None:
    ident = new_id("mem")
    assert ident.startswith("mem_")
    assert len(ident) == len("mem_") + 26


def test_new_id_rejects_empty_prefix() -> None:
    with pytest.raises(ValueError):
        new_id("")
