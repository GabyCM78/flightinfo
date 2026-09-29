"""Helpers that turn raw flight data from the API into readable text."""

from datetime import datetime, timezone
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


def get_time_info(flight):
    """Return the time block of a flight (arrivalTime or departureTime), or {}."""
    return flight.get("arrivalTime") or flight.get("departureTime") or {}


# Status for entries removed from the schedule ("ghost" entries).
DELETED_STATUS = "DEL"


def is_valid_flight(flight):
    """Return True if the flight is real and worth showing.

    Ghost entries are skipped: no flight id, no scheduled time, or status DEL.
    Cancelled flights (CAN) are kept, since travellers need to see them.
    Works for both arrivals (arrivalTime) and departures (departureTime).
    """
    if not isinstance(flight, dict):
        return False
    if not flight.get("flightId"):
        return False
    time_info = get_time_info(flight)
    if not time_info.get("scheduledUtc"):
        return False
    status_info = flight.get("locationAndStatus") or {}
    return status_info.get("flightLegStatus") != DELETED_STATUS


def is_upcoming(flight, now=None):
    """Return True if the flight has not landed/departed yet.

    Uses the estimated time if there is one, otherwise the scheduled time.
    A flight with an actual time has already happened.
    `now` must be timezone-aware; it defaults to the current UTC time
    (tests pass a fixed time so the result is always the same).
    """
    if not isinstance(flight, dict):
        return False
    time_info = get_time_info(flight)
    if time_info.get("actualUtc"):
        return False
    time_text = time_info.get("estimatedUtc") or time_info.get("scheduledUtc")
    if not time_text:
        return False
    try:
        flight_time = datetime.fromisoformat(time_text)
    except (TypeError, ValueError):
        return False
    if now is None:
        now = datetime.now(timezone.utc)
    return flight_time >= now
