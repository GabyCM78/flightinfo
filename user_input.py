"""Turns what the user types into clean values for the API. Returns None when the input is invalid."""

from datetime import date, datetime, timedelta

from config import AIRPORTS
from formatting import SWEDISH_TZ

# Words the user can type instead of a date: word -> days from today.
# Swedish words work too, like in the original app.
DATE_WORDS = {
    "today": 0, "idag": 0,
    "tomorrow": 1, "imorgon": 1,
    "yesterday": -1, "igår": -1,
}
NOW_WORDS = {"now", "nu"}


def parse_airport(text):
    """Return the IATA code for input like "arn", "Visby" or "Stockholm Arlanda", or None if unknown.

    "Stockholm" matches two airports; the first one in AIRPORTS (ARN) is used.
    """
    cleaned = text.strip()
    if not cleaned:
        return None
    if cleaned.upper() in AIRPORTS:
        return cleaned.upper()
    wanted = cleaned.lower()
    for code, name in AIRPORTS.items():
        name = name.lower()
        if wanted == name or wanted in name.split():
            return code
    return None


def parse_date(text, today=None):
    """Turn "now", "today", "tomorrow", "yesterday" or "YYYY-MM-DD" into (date, upcoming_only).

    "now" means today, but only flights that have not landed/departed yet.
    Returns None if the input is not a valid date. Tests can pass a fixed `today`.
    """
    if today is None:
        today = datetime.now(SWEDISH_TZ).date()
    word = text.strip().lower()
    if word in NOW_WORDS:
        return today, True
    if word in DATE_WORDS:
        return today + timedelta(days=DATE_WORDS[word]), False
    try:
        return date.fromisoformat(word), False
    except ValueError:
        return None


def parse_flight_id(text):
    """Turn input like "sk 532" or "SK-532" into "SK532". None unless it is 2-8 letters/digits (A-Z, 0-9)."""
    cleaned = text.replace(" ", "").replace("-", "").upper()
    if cleaned.isascii() and cleaned.isalnum() and 2 <= len(cleaned) <= 8:
        return cleaned
    return None
