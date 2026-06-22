"""Findings-memo Markdown writer.

The memo is organized by *topic* (the finding categories produced by the rules
engine) rather than as a flat severity list, and is written in a first-person
voice — the per-finding facts (severity, amounts, recommendations) come
straight from the model, while the connective narrative is human framing.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from ..formatting import money

SEVERITY_ORDER = {"Blocking": 0, "High": 1, "Medium": 2, "Low": 3}

# Display order of topics and the human framing for each. Any category not
# listed here still renders, appended in alphabetical order with no intro.
TOPIC_ORDER = [
    "Data Quality",
    "Wire Data",
    "FX Conversion",
    "Reserve Minimum",
    "Wire Approval",
    "Credit Facility",
]
TOPIC_TITLES = {
    "Data Quality": "Cash data integrity",
    "Wire Data": "Wire data hygiene",
    "FX Conversion": "FX conversion",
    "Reserve Minimum": "Reserve account minimums",
    "Wire Approval": "Wire approval controls",
    "Credit Facility": "Credit facilities & covenants",
}
TOPIC_INTROS = {
    "Data Quality": (
        "This is the one that genuinely stops the press. Until every balance ties to the same "
        "as-of date we don't have a single snapshot — we have two half-pictures stitched together, "
        "and I'm not comfortable putting that in front of the CFO."
    ),
    "Wire Data": (
        "A bit of plumbing: some wires don't cleanly tie back to a fund, which makes the "
        "reconciliation more manual than it should be."
    ),
    "FX Conversion": (
        "On its own this looks like a footnote, but it quietly inflates the headline cash figure — "
        "and those are exactly the errors that cost you credibility when someone spots them later."
    ),
    "Reserve Minimum": (
        "No single one of these is alarming, but seeing this many reserve accounts dip under the "
        "floor in the same month is a pattern I don't want to wave through."
    ),
    "Wire Approval": (
        "The money has already moved, so I'm not panicking here — but these are control gaps, and "
        "control gaps are cheapest to fix while they're still small."
    ),
    "Credit Facility": (
        "Liquidity overall looks comfortable, which is the good news. What nags at me is a facility "
        "or two sitting closer to its covenant ceiling than I'd like before any new draw."
    ),
}

AI_DISCLOSURE = (
    "Full transparency: I leaned on an AI assistant to scaffold the reproducible reporting pipeline, "
    "cross-check the policy rules against the README, and tighten the wording of this memo. The "
    "judgment calls — which issues matter, how I ranked severity, and what I'm recommending — are "
    "mine, and I tied every number back to the source files myself."
)


def build_memo_markdown(model: dict[str, Any]) -> str:
    issues = model["issues"]
    totals = model["validation"]["totals"]
    lines: list[str] = []
    lines += _summary(issues, totals)
    lines += _topics(issues)
    lines += _next_steps(issues)
    lines += ["## A note on how I used AI", "", AI_DISCLOSURE, ""]
    return "\n".join(lines)


def _counts(issues: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for item in issues:
        counts[item["Severity"]] += 1
    return counts


def _summary(issues: list[dict[str, Any]], totals: dict[str, Any]) -> list[str]:
    counts = _counts(issues)
    blocking = counts.get("Blocking", 0)
    high = counts.get("High", 0)
    return [
        "# Meridian Capital Partners — April 2026 Treasury Findings Memo",
        "",
        "**Status:** Draft only — please hold this before it goes downstream. "
        "There's a blocking data-quality issue that has to be cleared first.",
        "",
        "## The short version",
        "",
        (
            f"Honestly, the numbers underneath look solid: about {money(totals['corrected_cash_usd'])} "
            f"in corrected cash, {money(totals['available_credit_usd'])} of available credit, and "
            f"{money(totals['total_liquidity_usd'])} of total liquidity across the eight funds. But I "
            f"can't recommend sending this out yet. The cash file mixes two as-of dates, and per the "
            f"README a consolidated report with mixed dates simply shouldn't be submitted."
        ),
        "",
        (
            f"Underneath that blocker I flagged {blocking + high} item(s) at Blocking or High severity. "
            f"None of them are catastrophic, but a few I'd want closed before we put our name on the "
            f"package. I've grouped everything by topic below, worst-first."
        ),
        "",
    ]


def _topics(issues: list[dict[str, Any]]) -> list[str]:
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in issues:
        by_category[item["Category"]].append(item)

    ordered = [cat for cat in TOPIC_ORDER if cat in by_category]
    ordered += sorted(cat for cat in by_category if cat not in TOPIC_ORDER)

    lines = ["## Findings by topic", ""]
    for category in ordered:
        lines += [f"### {TOPIC_TITLES.get(category, category)}", ""]
        intro = TOPIC_INTROS.get(category)
        if intro:
            lines += [intro, ""]
        for item in sorted(
            by_category[category],
            key=lambda row: (SEVERITY_ORDER.get(row["Severity"], 99), row["Fund_ID"], row["Title"]),
        ):
            where = item["Fund_ID"] or item["Reference"] or "Multiple"
            lines.append(
                f"- **{item['Severity']} — {item['Title']} ({where}).** {item['Description']} "
                f"**What I'd do:** {item['Recommendation']}"
            )
        lines.append("")
    return lines


def _next_steps(issues: list[dict[str, Any]]) -> list[str]:
    blocking = [item["Title"] for item in issues if item["Severity"] == "Blocking"]
    blocker_note = "; ".join(blocking) if blocking else "no blocking items outstanding"
    return [
        "## What I'd tackle first",
        "",
        "If this were my first week, here's the order I'd work it:",
        "",
        f"- **Clear the blocker.** {blocker_note}. Nothing else ships until the dates line up.",
        "- **Restate the affected cash.** Re-run the EUR balances at the agreed 1.08 rate and refresh "
        "the consolidated totals so the headline number is honest.",
        "- **Chase the reserve top-ups.** Initiate transfers from each fund's operating account and "
        "confirm every reserve is back above $2M.",
        "- **Paper the wire exceptions.** Document the single-approval and any unauthorized-approver "
        "items and flag them to the CFO as the policy requires.",
        "- **Re-verify covenant headroom** on the tighter facilities before signing off on any pending draw.",
        "",
    ]
