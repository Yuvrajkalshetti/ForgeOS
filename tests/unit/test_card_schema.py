from __future__ import annotations

import pytest
from jsonschema import ValidationError

from forgeos.core.compression.schema import validate_card


def _valid_card() -> dict:
    return {
        "schema_version": 1,
        "card_id": "card:File:f1",
        "target": {"type": "File", "ref": "f1"},
        "generated_at": "2026-01-01T00:00:00+00:00",
        "source_hash": "abc",
        "provider": {"name": "forgeos", "model": "deterministic"},
        "purpose": "a file",
        "modules": [],
        "dependencies": [],
        "key_decisions": [],
        "risks": [],
        "recent_changes": [],
    }


def test_valid_card_passes() -> None:
    validate_card(_valid_card())


def test_extensions_block_is_allowed() -> None:
    card = _valid_card()
    card["extensions"] = {"x_qa": {"coverage": 0.9}}
    validate_card(card)


def test_missing_required_field_rejected() -> None:
    card = _valid_card()
    del card["purpose"]
    with pytest.raises(ValidationError):
        validate_card(card)


def test_unknown_top_level_key_rejected() -> None:
    card = _valid_card()
    card["bogus"] = 1
    with pytest.raises(ValidationError):
        validate_card(card)
