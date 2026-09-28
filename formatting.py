"""Helpers that turn raw flight data from the API into readable text."""

from datetime import datetime
from zoneinfo import ZoneInfo

SWEDISH_TZ = ZoneInfo("Europe/Stockholm")

# Shown when a value is missing (same symbol as the original app).
MISSING = "–"


def fmt_time(utc_text):
    """Format an API time like '2026-09-28T20:25:00Z' as '20:25 UTC → 22:25 CEST'.

    Returns MISSING if the time is missing or cannot be parsed.
    """
    if not utc_text:
        return MISSING
    try:
        utc_time = datetime.fromisoformat(utc_text)
    except (TypeError, ValueError):
        return MISSING
    local_time = utc_time.astimezone(SWEDISH_TZ)
    return f"{utc_time:%H:%M} UTC → {local_time:%H:%M} {local_time.tzname()}"
