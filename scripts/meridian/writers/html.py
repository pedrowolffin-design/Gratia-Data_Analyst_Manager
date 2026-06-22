"""Interactive single-file HTML report writer.

The markup/CSS/JS live in ``templates/report_template.html`` as a plain
``string.Template`` (``$placeholder`` slots). ``safe_substitute`` only touches
our named slots, leaving the JS ``${...}`` template literals untouched.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from string import Template
from typing import Any

from ..formatting import money

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "report_template.html"


def write_html(path: Path, model: dict[str, Any]) -> None:
    validation = model["validation"]
    totals = validation["totals"]
    issue_counts = validation["issue_counts_by_severity"]
    model_json = json.dumps(
        {
            "liquidity": model["liquidity"],
            "currency": model["currency"],
            "account_type": model["account_type"],
            "cash": model["cash"],
            "credit": model["credit"],
            "issues": model["issues"],
            "validation": validation,
        },
        sort_keys=True,
    )
    rendered = Template(TEMPLATE_PATH.read_text(encoding="utf-8")).safe_substitute(
        generated_at=html.escape(validation["generated_at"]),
        as_of_dates=html.escape(", ".join(validation["as_of_dates_found"])),
        as_of_count=len(validation["as_of_dates_found"]),
        corrected_cash=html.escape(money(totals["corrected_cash_usd"])),
        available_credit=html.escape(money(totals["available_credit_usd"])),
        total_liquidity=html.escape(money(totals["total_liquidity_usd"])),
        open_findings=len(model["issues"]),
        blocking_count=issue_counts.get("Blocking", 0),
        high_count=issue_counts.get("High", 0),
        model_json=model_json,
    )
    path.write_text(rendered, encoding="utf-8")
