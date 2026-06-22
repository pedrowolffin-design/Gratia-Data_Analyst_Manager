"""Assemble the consolidated treasury model from normalized inputs.

``build_model`` is the single entry point that the writers and tests consume.
It returns a dict whose keys (``cash``, ``credit``, ``wire``, ``issues``,
``liquidity``, ``currency``, ``account_type``, ``validation``) are a stable
contract — outputs and tests depend on these names.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from .config import FX_RATES
from .normalize import normalize_cash, normalize_credit, normalize_wires
from .period import ReportingPeriod, resolve_period
from .rules import build_issues


def build_model(inputs: dict[str, Any]) -> dict[str, Any]:
    cash_rows = normalize_cash(inputs["cash"])
    credit_rows = normalize_credit(inputs["credit"])
    wire_rows = normalize_wires(inputs["wire"])
    period = _resolve_period(inputs, cash_rows)
    issues = [
        issue.to_dict()
        for issue in build_issues(cash_rows, credit_rows, wire_rows, period.expected_as_of_date)
    ]
    liquidity = build_liquidity_summary(cash_rows, credit_rows)
    currency = aggregate(cash_rows, ["Fund_ID", "Fund_Name", "Currency"], "Corrected_Balance_USD")
    account_type = aggregate(cash_rows, ["Fund_ID", "Fund_Name", "Account_Type"], "Corrected_Balance_USD")
    validation = build_validation_summary(cash_rows, credit_rows, wire_rows, issues, liquidity, period)
    return {
        "period": {
            "label": period.label,
            "slug": period.slug,
            "expected_as_of_date": period.expected_as_of_date,
            "year": period.year,
            "month": period.month,
        },
        "cash": cash_rows,
        "credit": credit_rows,
        "wire": wire_rows,
        "issues": issues,
        "liquidity": liquidity,
        "currency": currency,
        "account_type": account_type,
        "validation": validation,
    }


def _resolve_period(inputs: dict[str, Any], cash_rows: list[dict[str, Any]]) -> ReportingPeriod:
    """Use the period resolved at load time, or derive one if absent."""
    period = inputs.get("period")
    if isinstance(period, ReportingPeriod):
        return period
    wire_name = inputs.get("paths", {}).get("wire", "")
    return resolve_period(wire_name, [row.get("As_Of_Date", "") for row in cash_rows])


def build_liquidity_summary(
    cash_rows: list[dict[str, Any]], credit_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    cash_by_fund: dict[str, float] = defaultdict(float)
    fund_names: dict[str, str] = {}
    for row in cash_rows:
        cash_by_fund[row["Fund_ID"]] += row["Corrected_Balance_USD"]
        fund_names[row["Fund_ID"]] = row["Fund_Name"]

    credit_by_fund = {row["Fund_ID"]: row for row in credit_rows}
    summary = []
    for fund_id in sorted(fund_names):
        credit = credit_by_fund.get(fund_id, {})
        available = float(credit.get("Available_USD", 0.0))
        corrected_cash = round(cash_by_fund[fund_id], 2)
        summary.append(
            {
                "Fund_ID": fund_id,
                "Fund_Name": fund_names[fund_id],
                "Corrected_Cash_USD": corrected_cash,
                "Available_Credit_USD": available,
                "Total_Liquidity_USD": round(corrected_cash + available, 2),
                "Current_LTV_Pct": credit.get("Current_LTV_Pct", ""),
                "Covenant_LTV_Max_Pct": credit.get("Covenant_LTV_Max_Pct", ""),
                "LTV_Headroom_Pct": credit.get("LTV_Headroom_Pct", ""),
            }
        )
    return summary


def aggregate(rows: list[dict[str, Any]], keys: list[str], amount_field: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], float] = defaultdict(float)
    for row in rows:
        grouped[tuple(row[key] for key in keys)] += row[amount_field]
    return [
        {**dict(zip(keys, key_tuple)), "Corrected_Balance_USD": round(amount, 2)}
        for key_tuple, amount in sorted(grouped.items())
    ]


def build_validation_summary(
    cash_rows: list[dict[str, Any]],
    credit_rows: list[dict[str, Any]],
    wire_rows: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    liquidity: list[dict[str, Any]],
    period: ReportingPeriod,
) -> dict[str, Any]:
    severities: dict[str, int] = defaultdict(int)
    for item in issues:
        severities[item["Severity"]] += 1
    corrected_cash = round(sum(row["Corrected_Balance_USD"] for row in cash_rows), 2)
    available_credit = round(sum(row["Available_USD"] for row in credit_rows), 2)
    total_liquidity = round(sum(row["Total_Liquidity_USD"] for row in liquidity), 2)
    expected_as_of_date = period.expected_as_of_date
    as_of_dates = sorted({row["As_Of_Date"] for row in cash_rows})
    stale_as_of_dates = [date for date in as_of_dates if date != expected_as_of_date]
    # Blocking findings drive the submission gate, so the status reflects the
    # data rather than a fixed assumption about this month.
    blocking_titles = list(dict.fromkeys(item["Title"] for item in issues if item["Severity"] == "Blocking"))
    if blocking_titles:
        submission_status = "BLOCKED - draft only"
        blocking_reason = f"{'; '.join(blocking_titles)} must be resolved before submission."
    else:
        submission_status = "Cleared for review"
        blocking_reason = ""
    return {
        "reporting_period": period.label,
        "expected_as_of_date": expected_as_of_date,
        "as_of_dates_found": as_of_dates,
        "stale_as_of_dates": stale_as_of_dates,
        "fund_count": len({row["Fund_ID"] for row in cash_rows}),
        "submission_status": submission_status,
        "blocking_reason": blocking_reason,
        "row_counts": {
            "cash": len(cash_rows),
            "credit": len(credit_rows),
            "wire": len(wire_rows),
            "issues": len(issues),
        },
        "issue_counts_by_severity": dict(sorted(severities.items())),
        "totals": {
            "corrected_cash_usd": corrected_cash,
            "available_credit_usd": available_credit,
            "total_liquidity_usd": total_liquidity,
        },
        "fx_rates": FX_RATES,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
