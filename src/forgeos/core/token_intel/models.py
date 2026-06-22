"""Token Intelligence models."""

from __future__ import annotations

import datetime

from pydantic import BaseModel, Field, computed_field

from forgeos._ids import new_id


class TokenEvent(BaseModel):
    """A single accounted token interaction (plan §11.3)."""

    id: str = Field(default_factory=lambda: new_id("tok"))
    request_id: str
    scope_ref: str
    provider: str
    model: str
    tokens_estimated: int = 0
    tokens_actual: int | None = None
    tokens_raw_equiv: int = 0
    tokens_saved: int = 0
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )


class TokenReport(BaseModel):
    """Aggregated savings across token events.

    ``raw_tokens`` is what naive context would have cost; ``compressed_tokens`` is
    what was actually billed/estimated; ``compression_ratio`` is compressed/raw
    (lower is better; 1.0 means no savings).
    """

    events: int = 0
    total_estimated: int = 0
    total_actual: int = 0
    total_raw_equiv: int = 0
    total_saved: int = 0
    saved_by_provider: dict[str, int] = Field(default_factory=dict)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def raw_tokens(self) -> int:
        return self.total_raw_equiv

    @computed_field  # type: ignore[prop-decorator]
    @property
    def compressed_tokens(self) -> int:
        return self.total_raw_equiv - self.total_saved

    @computed_field  # type: ignore[prop-decorator]
    @property
    def compression_ratio(self) -> float:
        if self.total_raw_equiv == 0:
            return 1.0
        return round(self.compressed_tokens / self.total_raw_equiv, 4)
