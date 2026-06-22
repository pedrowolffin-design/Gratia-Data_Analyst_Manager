"""Policy-based validation: turn normalized rows into a list of findings.

Every check maps to a specific README policy (FX rates, reserve minimums, wire
approval tiers, covenant verification, data-quality as-of dates). Findings are
modeled as :class:`Issue` instances and serialized to dicts by the model layer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .config import (
    DUAL_APPROVAL_THRESHOLD_USD,
    FX_RATES,
    RESERVE_MINIMUM_USD,
)
from .formatting import money, pct


@dataclass(frozen=True)
class Issue:
    """A single finding. Field names map 1:1 to the report column headers."""

    Severity: str
    Category: str
    Title: str
    Description: str
    Why_It_Matters: str
    Recommendation: str
    Fund_ID: str
    Reference: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _approvers(wire_row: dict[str, Any]) -> str:
    """Human-readable approver list for a wire, for use in finding descriptions."""
    return ", ".join(wire_row["Approvers"]) or "none recorded"


def build_issues(
    cash_rows: list[dict[str, Any]],
    credit_rows: list[dict[str, Any]],
    wire_rows: list[dict[str, Any]],
    expected_as_of_date: str,
) -> list[Issue]:
    issues: list[Issue] = []
    issues.extend(_data_quality_issues(cash_rows, expected_as_of_date))
    issues.extend(_fx_issues(cash_rows))
    issues.extend(_reserve_issues(cash_rows))
    issues.extend(_wire_issues(wire_rows, credit_rows))
    issues.extend(_credit_issues(credit_rows))
    return issues


def _data_quality_issues(
    cash_rows: list[dict[str, Any]], expected_as_of_date: str
) -> list[Issue]:
    dates = sorted({row["As_Of_Date"] for row in cash_rows})
    if dates == [expected_as_of_date]:
        return []
    stale_rows = [row for row in cash_rows if row["As_Of_Date"] != expected_as_of_date]
    return [
        Issue(
            Severity="Blocking",
            Category="Data Quality",
            Title="Mixed cash as-of dates",
            Description=(
                f"Cash positions include dates {', '.join(dates)}; "
                f"{len(stale_rows)} row(s) are not {expected_as_of_date}."
            ),
            Why_It_Matters="The README states consolidated reports with mixed dates must not be submitted.",
            Recommendation="Refresh the stale cash balance(s), document the gap, and update the CFO with an expected resolution timeline.",
            Fund_ID=stale_rows[0]["Fund_ID"] if stale_rows else "",
            Reference="Multiple",
        )
    ]


def _fx_issues(cash_rows: list[dict[str, Any]]) -> list[Issue]:
    fx_mismatches = [row for row in cash_rows if abs(row["USD_Variance"]) > 0.01]
    if not fx_mismatches:
        return []
    total_overstatement = sum(row["USD_Variance"] for row in fx_mismatches)
    fund_ids = sorted({row["Fund_ID"] for row in fx_mismatches})
    currencies = sorted({row["Currency"] for row in fx_mismatches})
    funds_label = ", ".join(fund_ids)
    rate_label = ", ".join(f"{FX_RATES[code]} {code}/USD" for code in currencies)
    return [
        Issue(
            Severity="High",
            Category="FX Conversion",
            Title=f"{funds_label} balances use incorrect USD conversion",
            Description=(
                f"{len(fx_mismatches)} {'/'.join(currencies)} row(s) are overstated by "
                f"{money(total_overstatement)} versus the CFO-approved rate(s) ({rate_label})."
            ),
            Why_It_Matters="Using non-approved FX corrupts consolidated USD cash and liquidity reporting.",
            Recommendation="Recalculate USD balances from local currency using the fixed README rates and confirm source-system FX mapping.",
            Fund_ID=fund_ids[0],
            Reference="Cash",
        )
    ]


def _reserve_issues(cash_rows: list[dict[str, Any]]) -> list[Issue]:
    issues: list[Issue] = []
    for row in cash_rows:
        if row["Account_Type"] != "Reserve" or row["Corrected_Balance_USD"] >= RESERVE_MINIMUM_USD:
            continue
        shortfall = RESERVE_MINIMUM_USD - row["Corrected_Balance_USD"]
        issues.append(
            Issue(
                Severity="High",
                Category="Reserve Minimum",
                Title=f"{row['Fund_ID']} reserve account below $2M minimum",
                Description=(
                    f"{row['Bank']} {row['Account_Number']} has {money(row['Corrected_Balance_USD'])}, "
                    f"short by {money(shortfall)}."
                ),
                Why_It_Matters="Treasury policy requires every designated reserve account to maintain at least $2M at all times.",
                Recommendation="Initiate top-up from the fund operating account and confirm completion.",
                Fund_ID=row["Fund_ID"],
                Reference=row["Account_Number"],
            )
        )
    return issues


def _wire_issues(
    wire_rows: list[dict[str, Any]], credit_rows: list[dict[str, Any]]
) -> list[Issue]:
    issues: list[Issue] = []
    for row in wire_rows:
        if row["Amount_USD"] > DUAL_APPROVAL_THRESHOLD_USD and row["Approver_Count"] < 2:
            issues.append(
                Issue(
                    Severity="High",
                    Category="Wire Approval",
                    Title="Wire above $5M completed with single approval",
                    Description=(
                        f"{row['Reference']} for {money(row['Amount_USD'])} from "
                        f"{row['Parsed_Fund_ID']} had {row['Approver_Count']} approver "
                        f"(sole approver: {_approvers(row)})."
                    ),
                    Why_It_Matters="The README requires dual approval above $5M and CFO reporting for exceptions.",
                    Recommendation="Report the exception to the CFO and obtain/document retroactive review.",
                    Fund_ID=row["Parsed_Fund_ID"] or "",
                    Reference=row["Reference"],
                )
            )
        if row["Unknown_Approvers"]:
            issues.append(
                Issue(
                    Severity="High",
                    Category="Wire Approval",
                    Title="Wire includes unauthorized approver",
                    Description=(
                        f"{row['Reference']} includes unknown approver(s): "
                        f"{', '.join(row['Unknown_Approvers'])}. Full approval chain: {_approvers(row)}."
                    ),
                    Why_It_Matters="All wire approvals must come from the authorized signer list.",
                    Recommendation="Validate approver authority before execution or document remediation.",
                    Fund_ID=row["Parsed_Fund_ID"] or "",
                    Reference=row["Reference"],
                )
            )
        if row["Parsed_Fund_ID"] is None:
            issues.append(
                Issue(
                    Severity="Blocking",
                    Category="Wire Data",
                    Title="Wire fund ID could not be parsed",
                    Description=f"{row['Reference']} From_Account value is '{row['From_Account']}'.",
                    Why_It_Matters="Wire activity cannot be tied back to fund liquidity.",
                    Recommendation="Correct the source account naming or add an explicit Fund_ID field.",
                    Fund_ID="",
                    Reference=row["Reference"],
                )
            )

    for row in wire_rows:
        if row["Status"] == "Pending" and "drawdown" in row["Purpose"].lower():
            credit = next((item for item in credit_rows if item["Fund_ID"] == row["Parsed_Fund_ID"]), None)
            detail = f"{row['Reference']} is a pending {money(row['Amount_USD'])} facility draw."
            if credit:
                detail += (
                    f" Current LTV is {pct(credit['Current_LTV_Pct'])} versus "
                    f"{pct(credit['Covenant_LTV_Max_Pct'])} max."
                )
            issues.append(
                Issue(
                    Severity="High",
                    Category="Credit Facility",
                    Title="Pending facility draw requires covenant verification",
                    Description=detail,
                    Why_It_Matters="The README requires covenant compliance verification before any new drawdown is approved.",
                    Recommendation="Hold approval until LTV is recalculated with updated uncalled commitments or a lender waiver is documented.",
                    Fund_ID=row["Parsed_Fund_ID"] or "",
                    Reference=row["Reference"],
                )
            )
    return issues


def _credit_issues(credit_rows: list[dict[str, Any]]) -> list[Issue]:
    issues: list[Issue] = []
    for row in credit_rows:
        if row["LTV_Headroom_Pct"] <= 3:
            issues.append(
                Issue(
                    Severity="Medium",
                    Category="Credit Facility",
                    Title=f"{row['Fund_ID']} has limited LTV headroom",
                    Description=(
                        f"Current LTV is {pct(row['Current_LTV_Pct'])} versus {pct(row['Covenant_LTV_Max_Pct'])} max, "
                        f"leaving {pct(row['LTV_Headroom_Pct'])} headroom."
                    ),
                    Why_It_Matters="Limited headroom increases the risk that a new draw or valuation movement creates a covenant breach.",
                    Recommendation="Reconfirm borrowing base data before further draws and monitor covenant headroom daily.",
                    Fund_ID=row["Fund_ID"],
                    Reference=row["Lender"],
                )
            )
        if abs(row["Facility_Math_Variance_USD"]) > 0.01:
            issues.append(
                Issue(
                    Severity="High",
                    Category="Credit Facility",
                    Title=f"{row['Fund_ID']} facility availability does not reconcile",
                    Description=f"Facility size less drawn amount differs from reported availability by {money(row['Facility_Math_Variance_USD'])}.",
                    Why_It_Matters="Facility capacity is part of total liquidity and must reconcile.",
                    Recommendation="Resolve facility data with lender statement before publishing liquidity totals.",
                    Fund_ID=row["Fund_ID"],
                    Reference=row["Lender"],
                )
            )
    return issues
