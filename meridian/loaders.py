"""Locate and read the raw treasury case CSV inputs."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .period import resolve_period


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def data_dir(root: Path) -> Path:
    candidate = root / "Gratia-Data_Analyst_Manager"
    return candidate if candidate.exists() else root


def find_input_file(base: Path, pattern: str) -> Path:
    matches = sorted(base.glob(f"*{pattern}"))
    if not matches:
        raise FileNotFoundError(f"Could not find input matching *{pattern} in {base}")
    return matches[0]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def load_inputs(root: Path | None = None) -> dict[str, Any]:
    root = root or project_root()
    base = data_dir(root)
    paths = {
        "cash": find_input_file(base, "Fund Cash Positions.csv"),
        "credit": find_input_file(base, "Credit Facility Summary.csv"),
        # Match any month's wire log (e.g. "Wire Transfer Log (April 2026).csv");
        # the reporting period is derived from this filename.
        "wire": find_input_file(base, "Wire Transfer Log*.csv"),
    }
    cash = read_csv(paths["cash"])
    period = resolve_period(paths["wire"].name, [row.get("As_Of_Date", "") for row in cash])
    return {
        "paths": {key: str(value) for key, value in paths.items()},
        "period": period,
        "cash": cash,
        "credit": read_csv(paths["credit"]),
        "wire": read_csv(paths["wire"]),
    }
