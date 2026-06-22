"""Parse raw CSV strings into typed, enriched rows.

Each ``normalize_*`` function takes the raw ``DictReader`` rows for one input
and returns rows augmented with derived fields (USD corrections, variances,
parsed approvers, etc.) that the rules and writers depend on.
"""

from __future__ import annotations

from typing import Any

from .config import AUTHORIZED_SIGNERS, FX_RATES, FUND_RE


def parse_float(row: dict[str, str], field: str) -> float:
    return float(row[field])


def parse_approvers(value: str) -> list[str]:
    return [part.strip() for part in value.split(";") if part.strip()]


def parse_wire_fund_id(from_account: str) -> str | None:
    match = FUND_RE.match(from_account)
    return match.group(1) if match else None


def normalize_cash(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    normalized = []
    for row in rows:
        currency = row["Currency"]
        local = parse_float(row, "Balance_Local")
        reported = parse_float(row, "Balance_USD")
        corrected = round(local * FX_RATES[currency], 2)
        normalized.append(
            {
                **row,
                "Balance_Local": local,
                "Reported_Balance_USD": reported,
                "Corrected_Balance_USD": corrected,
                "USD_Variance": round(reported - corrected, 2),
                "FX_Rate_Used": FX_RATES[currency],
            }
        )
    return normalized


def normalize_credit(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    normalized = []
    for row in rows:
        size = parse_float(row, "Facility_Size_USD")
        drawn = parse_float(row, "Drawn_Amount_USD")
        available = parse_float(row, "Available_USD")
        covenant = parse_float(row, "Covenant_LTV_Max_Pct")
        current = parse_float(row, "Current_LTV_Pct")
        normalized.append(
            {
                **row,
                "Facility_Size_USD": size,
                "Drawn_Amount_USD": drawn,
                "Available_USD": available,
                "Covenant_LTV_Max_Pct": covenant,
                "Current_LTV_Pct": current,
                "LTV_Headroom_Pct": round(covenant - current, 2),
                "Facility_Math_Variance_USD": round(size - drawn - available, 2),
            }
        )
    return normalized


def normalize_wires(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    normalized = []
    for row in rows:
        approvers = parse_approvers(row["Approved_By"])
        normalized.append(
            {
                **row,
                "Amount_USD": parse_float(row, "Amount_USD"),
                "Parsed_Fund_ID": parse_wire_fund_id(row["From_Account"]),
                "Approver_Count": len(approvers),
                "Approvers": approvers,
                "Unknown_Approvers": [name for name in approvers if name not in AUTHORIZED_SIGNERS],
            }
        )
    return normalized
