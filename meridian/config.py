"""Treasury policy constants for the Meridian treasury case.

These values come directly from the README ("Treasury Operations Context") and
are the single source of truth for the validation rules applied downstream. The
reporting period and its expected month-end as-of date are *not* here — they are
derived per run from the input files (see :mod:`meridian.period`).
"""

from __future__ import annotations

import re

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
