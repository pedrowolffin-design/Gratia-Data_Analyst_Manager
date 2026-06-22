"""Derive the reporting period (month/year) from the input files.

Everything time-specific in the deliverables — report titles, output filenames,
and the expected month-end as-of date used by the data-quality rule — flows from
a single :class:`ReportingPeriod`. That makes the pipeline reproducible: drop in
a different month's input files and the reports regenerate for that month with no
code changes.

The period is read from the wire-log filename (e.g. ``Wire Transfer Log
(April 2026).csv``); if that filename carries no ``(Month Year)`` marker we fall
back to the latest as-of date present in the cash data.
"""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass

# Month name (lower-case) -> month number, e.g. {"april": 4}.
_MONTHS = {name.lower(): num for num, name in enumerate(calendar.month_name) if name}
# Matches a "(April 2026)" style marker anywhere in an input filename.
_FILENAME_PERIOD_RE = re.compile(r"\(\s*([A-Za-z]+)\s+(\d{4})\s*\)")
# Matches a leading YYYY-MM-DD date in an as-of-date cell.
_ISO_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


@dataclass(frozen=True)
class ReportingPeriod:
    """The single calendar month a report covers."""

    year: int
    month: int

    @property
    def label(self) -> str:
        """Human-readable period, e.g. ``"April 2026"``."""
        return f"{calendar.month_name[self.month]} {self.year}"

    @property
    def slug(self) -> str:
        """Filename-safe period, e.g. ``"april_2026"``."""
        return f"{calendar.month_name[self.month].lower()}_{self.year}"

    @property
    def expected_as_of_date(self) -> str:
        """The month-end date every cash row should carry, e.g. ``"2026-04-30"``."""
        last_day = calendar.monthrange(self.year, self.month)[1]
        return f"{self.year:04d}-{self.month:02d}-{last_day:02d}"


def period_from_filename(name: str) -> ReportingPeriod | None:
    match = _FILENAME_PERIOD_RE.search(name)
    if not match:
        return None
    month = _MONTHS.get(match.group(1).lower())
    if not month:
        return None
    return ReportingPeriod(year=int(match.group(2)), month=month)


def period_from_dates(dates: list[str]) -> ReportingPeriod | None:
    year_months = sorted(
        {(int(m.group(1)), int(m.group(2))) for value in dates if (m := _ISO_DATE_RE.search(value))}
    )
    if not year_months:
        return None
    year, month = year_months[-1]  # latest year-month present in the data
    return ReportingPeriod(year=year, month=month)


def resolve_period(wire_filename: str, cash_dates: list[str]) -> ReportingPeriod:
    """Determine the reporting period from the wire filename, falling back to data."""
    period = period_from_filename(wire_filename) or period_from_dates(cash_dates)
    if period is None:
        raise ValueError(
            "Could not determine the reporting period from wire filename "
            f"{wire_filename!r} or cash as-of dates {cash_dates!r}. Ensure the wire "
            "log filename includes a (Month Year) marker or the cash data carries "
            "YYYY-MM-DD as-of dates."
        )
    return period
