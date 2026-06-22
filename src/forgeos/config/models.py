"""Typed configuration models.

These describe the full ForgeOS configuration surface. Every field has a safe
default so a zero-config install still runs; layers (user/project/env) override
only what they specify. See ``loader.py`` for precedence rules.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ClaudeConfig(BaseModel):
    """Anthropic Claude provider settings (reference cloud adapter)."""

    model: str = "claude-opus-4-8"
    max_tokens: int = 1024
    api_key_env: str = "ANTHROPIC_API_KEY"


class OllamaConfig(BaseModel):
    """Ollama provider settings (reference local adapter)."""

    model: str = "llama3.1"
    host: str = "http://localhost:11434"


class ProvidersConfig(BaseModel):
    """Provider layer configuration. ``default`` selects the active provider."""

    default: str = "claude"
    claude: ClaudeConfig = Field(default_factory=ClaudeConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)


class TokensConfig(BaseModel):
    """Token budgets used by the Context Assembly + Token Intelligence engines.

    ``None`` means unbounded for that scope.
    """

    per_request: int | None = 8000
    per_session: int | None = None
    per_project: int | None = None


class ConcurrencyConfig(BaseModel):
    """Bounded-concurrency limits for the agent orchestrator."""

    global_limit: int = 5
    per_provider: dict[str, int] = Field(default_factory=lambda: {"ollama": 2})


class LoggingConfig(BaseModel):
    """Structured logging configuration.

    The config key is ``json`` (via alias); the attribute is ``as_json`` to avoid
    shadowing :meth:`pydantic.BaseModel.json`.
    """

    model_config = ConfigDict(populate_by_name=True)

    level: str = "INFO"
    as_json: bool = Field(default=True, alias="json")


class ForgeConfig(BaseModel):
    """Root configuration object assembled from all layers."""

    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    tokens: TokensConfig = Field(default_factory=TokensConfig)
    concurrency: ConcurrencyConfig = Field(default_factory=ConcurrencyConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
