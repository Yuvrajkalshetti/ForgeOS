"""Ports — abstract interfaces that the core domain depends on.

The core never imports adapters; it depends only on these protocols. Concrete
adapters (SQLite, Claude, Ollama, CLI, MCP, tokenizers) implement them.
"""

from __future__ import annotations

from forgeos.ports.provider import (
    Message,
    ProviderPort,
    ProviderRequest,
    ProviderResult,
    Usage,
)
from forgeos.ports.storage import Record, StoragePort
from forgeos.ports.tokenizer import TokenizerPort
from forgeos.ports.transport import TransportPort
from forgeos.ports.vector import VectorMatch, VectorPort

__all__ = [
    "Message",
    "ProviderPort",
    "ProviderRequest",
    "ProviderResult",
    "Record",
    "StoragePort",
    "TokenizerPort",
    "TransportPort",
    "Usage",
    "VectorMatch",
    "VectorPort",
]
