"""Transport port.

A transport (CLI, MCP stdio, later REST) exposes the same application services.
No business logic lives in a transport; it only adapts an external protocol to
service calls, which is what guarantees CLI/MCP parity.
"""

from __future__ import annotations

from typing import Protocol


class TransportPort(Protocol):
    """An entrypoint that drives ForgeOS services over some protocol."""

    name: str

    def run(self) -> None:
        """Start the transport (e.g. parse argv, or serve an MCP stdio loop)."""
        ...
