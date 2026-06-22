"""Meridian treasury reporting pipeline (standard library only).

The reporting period is derived per run from the input filenames (see
:mod:`meridian.period`), so the same code reproduces a report for any month.

Public API re-exported here is the stable contract consumed by the ``python -m
meridian`` entry point and the test suite.
"""

from __future__ import annotations

from .cli import main
from .formatting import money, pct
from .loaders import load_inputs, project_root
from .model import build_model
from .normalize import parse_wire_fund_id

__all__ = [
    "build_model",
    "load_inputs",
    "main",
    "money",
    "parse_wire_fund_id",
    "pct",
    "project_root",
]
