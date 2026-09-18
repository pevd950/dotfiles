"""Shared types for notify-user provider adapters."""

from __future__ import annotations

from dataclasses import dataclass


class ValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    status: str
    detail: str
