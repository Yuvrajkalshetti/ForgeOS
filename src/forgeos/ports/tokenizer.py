"""Tokenizer port.

Dual-source token accounting: a local estimator gives pre-flight counts for
budgeting (Context Assembly), while provider-reported usage is the authoritative
actual after a call. Both implement this interface.
"""

from __future__ import annotations

from typing import Protocol

from forgeos.ports.provider import Message


class TokenizerPort(Protocol):
    """Estimate token counts for text and message lists."""

    def count_text(self, text: str, model: str | None = None) -> int:
        """Return the token count for ``text``."""
        ...

    def count_messages(self, messages: list[Message], model: str | None = None) -> int:
        """Return the token count for a list of messages."""
        ...
