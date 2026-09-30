"""Destination overview: how many flights go to (or come from) each city, with the country."""

import json
import re
from collections import Counter
from pathlib import Path

CITY_COUNTRY_FILE = Path(__file__).parent / "city_country.json"
UNKNOWN_COUNTRY = "Unknown"

# An airport code at the end of a name, e.g. " LHR" in "London LHR".
AIRPORT_CODE_AT_END = re.compile(r" [A-Z]{3}$")


def load_city_country(path=CITY_COUNTRY_FILE):
    """Read city_country.json: {"Frankfurt": "Germany", ...}."""
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def city_name(airport_name):
    """Remove an airport code at the end: "London LHR" -> "London", "Frankfurt" -> "Frankfurt"."""
    return AIRPORT_CODE_AT_END.sub("", airport_name).strip()


def other_end(flight):
    """The other airport of a flight: the destination of a departure, the origin of an arrival."""
    return flight.get("arrivalAirportEnglish") or flight.get("departureAirportEnglish")


def count_destinations(flights):
    """Count flights per city, e.g. Counter({"Oslo": 20, "London": 12})."""
    return Counter(city_name(name) for name in map(other_end, flights) if name)


def format_destinations(counts, city_country, text_filter=""):
    """Lines like "Frankfurt (5 flights) [Germany]", most flights first.

    text_filter keeps only lines where the city or the country contains the text (any case).
    """
    wanted = text_filter.strip().lower()
    lines = []
    for city, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        country = city_country.get(city, UNKNOWN_COUNTRY)
        if wanted and wanted not in city.lower() and wanted not in country.lower():
            continue
        unit = "flight" if count == 1 else "flights"
        lines.append(f"{city} ({count} {unit}) [{country}]")
    return lines
