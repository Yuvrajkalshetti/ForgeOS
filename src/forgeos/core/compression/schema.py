"""JSON Schema for knowledge cards (plan §9.2).

Core fields are required; unknown top-level keys are rejected, but ``extensions``
is an open object for project-defined ``x_*`` blocks.
"""

from __future__ import annotations

from typing import Any

import jsonschema

CARD_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "forgeos.knowledge_card",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_version",
        "card_id",
        "target",
        "generated_at",
        "source_hash",
        "provider",
        "purpose",
        "modules",
        "dependencies",
        "key_decisions",
        "risks",
        "recent_changes",
    ],
    "properties": {
        "schema_version": {"type": "integer", "const": 1},
        "card_id": {"type": "string", "minLength": 1},
        "target": {
            "type": "object",
            "additionalProperties": False,
            "required": ["type", "ref"],
            "properties": {"type": {"type": "string"}, "ref": {"type": "string"}},
        },
        "generated_at": {"type": "string"},
        "source_hash": {"type": "string"},
        "provider": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "model"],
            "properties": {"name": {"type": "string"}, "model": {"type": "string"}},
        },
        "purpose": {"type": "string"},
        "modules": {"type": "array"},
        "dependencies": {"type": "array"},
        "key_decisions": {"type": "array"},
        "risks": {"type": "array"},
        "recent_changes": {"type": "array"},
        "extensions": {"type": "object"},
    },
}


def validate_card(card: dict[str, Any]) -> None:
    """Raise :class:`jsonschema.ValidationError` if ``card`` violates the schema."""
    jsonschema.validate(card, CARD_SCHEMA)
