"""Treasury policy constants for the Meridian April 2026 case.

These values come directly from the README ("Treasury Operations Context") and
are the single source of truth for the validation rules applied downstream.
"""

from __future__ import annotations

import re

EXPECTED_AS_OF_DATE = "2026-04-30"
FX_RATES = {"USD": 1.0, "EUR": 1.08, "GBP": 1.27}
AUTHORIZED_SIGNERS = {
    "J. Chen",
    "R. Patel",
    "M. Torres",
    "A. Novak",
    "S. Kim",
}
RESERVE_MINIMUM_USD = 2_000_000.0
DUAL_APPROVAL_THRESHOLD_USD = 5_000_000.0
FUND_RE = re.compile(r"^(MF-\d{3})\b")
