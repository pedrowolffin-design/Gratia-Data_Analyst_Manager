"""Shared display formatting helpers."""

from __future__ import annotations


def money(value: float) -> str:
    return f"${value:,.0f}"


def pct(value: float) -> str:
    return f"{value:.1f}%"
