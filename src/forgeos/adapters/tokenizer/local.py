"""Local token estimator — a deterministic pre-flight :class:`TokenizerPort`.

A dependency-free heuristic (~4 characters per token) used for budgeting before a
call. Provider-reported usage is the authoritative actual afterward; both feed the
ledger's dual-source reconciliation.
"""

from __future__ import annotations

from forgeos.ports.provider import Message

_CHARS_PER_TOKEN = 4


class LocalEstimator:
    """Estimate tokens from text length. Stable and offline."""

    name = "local-estimator"

    def count_text(self, text: str, model: str | None = None) -> int:
        if not text:
            return 0
        return (len(text) + _CHARS_PER_TOKEN - 1) // _CHARS_PER_TOKEN

    def count_messages(self, messages: list[Message], model: str | None = None) -> int:
        return sum(self.count_text(m.content, model) for m in messages)
