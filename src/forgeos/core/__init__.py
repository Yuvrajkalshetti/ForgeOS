"""ForgeOS core domain.

Pure domain logic. ``core`` depends only on ``forgeos.ports`` and other ``core``
modules — never on ``forgeos.adapters`` (hexagonal invariant, ADR 0001).
"""

from __future__ import annotations
