"""Date helpers for holding periods (policy section 4)."""

from __future__ import annotations

from datetime import date


def add_years(d: date, years: int) -> date:
    """Same calendar day ``years`` later; 29 February maps to 28 February."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(year=d.year + years, day=28)


def is_long_term(holding_start: date, date_sold: date) -> bool:
    """Long term means held for more than one year: sold after the anniversary."""
    return date_sold > add_years(holding_start, 1)


def parse_date(text: str) -> date:
    return date.fromisoformat(text.strip())
