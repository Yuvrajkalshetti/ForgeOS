"""Structured logging.

A single ``request_id`` correlates a CLI/MCP invocation through services and
provider calls — the backbone of the Observability Strategy (plan §13). Logs are
emitted as JSON by default so they can be parsed without an external stack.
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
from typing import Any

from forgeos._ids import new_id

_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "forgeos_request_id", default=None
)

_LOGGER_NAMESPACE = "forgeos"


class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON including the active request id."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": _request_id.get(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        extra = getattr(record, "context", None)
        if isinstance(extra, dict):
            payload["context"] = extra
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO", json_output: bool = True) -> None:
    """Configure the ForgeOS logger namespace. Idempotent (replaces handlers)."""
    logger = logging.getLogger(_LOGGER_NAMESPACE)
    logger.setLevel(level.upper())
    logger.handlers.clear()
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(JsonFormatter() if json_output else logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the ForgeOS namespace."""
    return logging.getLogger(f"{_LOGGER_NAMESPACE}.{name}")


def set_request_id(request_id: str | None) -> None:
    """Bind ``request_id`` to the current context for log correlation."""
    _request_id.set(request_id)


def new_request_id() -> str:
    """Generate, bind, and return a fresh request id."""
    request_id = new_id("req")
    _request_id.set(request_id)
    return request_id
