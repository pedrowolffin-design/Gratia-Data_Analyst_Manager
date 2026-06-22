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


def _signed_money(value: float) -> str:
    """Money with an explicit +/- sign, for the correction delta."""
    sign = "+" if value >= 0 else "-"
    return f"{sign}{money(abs(value))}"


def _status_panel(validation: dict[str, Any]) -> dict[str, str]:
    """Header status-panel copy derived from the run's submission gate."""
    if validation["submission_status"].upper().startswith("BLOCKED"):
        stale = ", ".join(validation.get("stale_as_of_dates") or [])
        if stale:
            note = (
                f"The consolidated package contains stale cash row(s) dated {stale}. "
                "Refresh before sending the report downstream."
            )
        else:
            note = validation.get("blocking_reason") or "Resolve blocking findings before sending downstream."
        return {"label": "Draft / blocked", "title": "Do not submit yet", "note": note}
    return {
        "label": "Cleared for review",
        "title": "Ready for CFO review",
        "note": "All automated checks passed. Verify the figures against source before distribution.",
    }


def write_html(path: Path, model: dict[str, Any]) -> None:
    validation = model["validation"]
    totals = validation["totals"]
    issue_counts = validation["issue_counts_by_severity"]
    status = _status_panel(validation)
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
        period_label=html.escape(model["period"]["label"]),
        fund_count=validation["fund_count"],
        status_label=html.escape(status["label"]),
        status_title=html.escape(status["title"]),
        status_note=html.escape(status["note"]),
        generated_at=html.escape(validation["generated_at"]),
        as_of_dates=html.escape(", ".join(validation["as_of_dates_found"])),
        as_of_count=len(validation["as_of_dates_found"]),
        reported_cash=html.escape(money(totals["reported_cash_usd"])),
        cash_correction=html.escape(_signed_money(totals["cash_correction_usd"])),
        corrected_cash=html.escape(money(totals["corrected_cash_usd"])),
        available_credit=html.escape(money(totals["available_credit_usd"])),
        total_liquidity=html.escape(money(totals["total_liquidity_usd"])),
        open_findings=len(model["issues"]),
        blocking_count=issue_counts.get("Blocking", 0),
        high_count=issue_counts.get("High", 0),
        model_json=model_json,
    )
    path.write_text(rendered, encoding="utf-8")
