"""Turns what the user types into clean values for the API. Returns None when the input is invalid."""

from config import AIRPORTS


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
