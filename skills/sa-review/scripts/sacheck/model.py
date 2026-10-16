"""Shared value types for sa-design-kit checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Severity = Literal["error", "warn"]


@dataclass(frozen=True)
class Finding:
    """One check result: which rule, how serious, where, and what is wrong."""

    rule: str
    severity: Severity
    file: str
    item: str
    message: str
