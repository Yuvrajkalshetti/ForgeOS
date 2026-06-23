"""Ownership Intelligence (V2, E4 — ADR 0016): declared + observed ownership."""

from __future__ import annotations

from forgeos.core.ownership_intel.classifier import classify, declared_domain
from forgeos.core.ownership_intel.models import OwnershipResult, OwnershipRule
from forgeos.core.ownership_intel.rules import DEFAULT_RULES, load_rules
from forgeos.core.ownership_intel.summary import runtime_summary

__all__ = [
    "DEFAULT_RULES",
    "OwnershipResult",
    "OwnershipRule",
    "classify",
    "declared_domain",
    "load_rules",
    "runtime_summary",
]
