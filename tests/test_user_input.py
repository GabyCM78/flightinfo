"""Tests for user_input.py. Pure logic, no API calls."""

from datetime import date, datetime

import pytest

from formatting import SWEDISH_TZ
from user_input import parse_airport, parse_date, parse_flight_id

# A fixed "today", so the date tests give the same result every day.
TODAY = date(2026, 9, 29)


# --- parse_airport ----------------------------------------------------------

@pytest.mark.parametrize(
    "text, expected",
    [
        ("ARN", "ARN"),  # IATA code
        ("arn", "ARN"),  # lower case
        ("  got  ", "GOT"),  # spaces around
        ("Visby", "VBY"),  # city name
        ("arlanda", "ARN"),  # one word of the name
        ("GÖTEBORG", "GOT"),  # upper case with a Swedish letter
        ("Östersund", "OSD"),
        ("Stockholm Arlanda", "ARN"),  # the full name
        ("stockholm", "ARN"),  # matches ARN and BMA: the first one (ARN) wins
        ("bromma", "BMA"),
    ],
)
def test_parse_airport_finds_the_code(text, expected):
    assert parse_airport(text) == expected


@pytest.mark.parametrize("text", ["", "   ", "XXX", "a", "Oslo"])
def test_parse_airport_returns_none_for_unknown(text):
    assert parse_airport(text) is None


# --- parse_date -------------------------------------------------------------

@pytest.mark.parametrize(
    "text, expected",
    [
        ("now", (TODAY, True)),  # today, but only upcoming flights
        ("nu", (TODAY, True)),  # Swedish, like the original
        ("today", (TODAY, False)),
        ("idag", (TODAY, False)),
        ("  TODAY ", (TODAY, False)),  # spaces and upper case
        ("tomorrow", (date(2026, 9, 30), False)),
        ("imorgon", (date(2026, 9, 30), False)),
        ("yesterday", (date(2026, 9, 28), False)),
        ("igår", (date(2026, 9, 28), False)),
        ("2026-10-05", (date(2026, 10, 5), False)),  # an exact date
    ],
)
def test_parse_date(text, expected):
    assert parse_date(text, today=TODAY) == expected


def test_tomorrow_crosses_the_month_end():
    assert parse_date("tomorrow", today=date(2026, 9, 30)) == (date(2026, 10, 1), False)


@pytest.mark.parametrize("text", ["2026-02-30", "29/9", "", "next week"])
def test_parse_date_returns_none_for_invalid(text):
    assert parse_date(text, today=TODAY) is None


def test_parse_date_uses_swedish_today_by_default():
    assert parse_date("today") == (datetime.now(SWEDISH_TZ).date(), False)


# --- parse_flight_id --------------------------------------------------------

@pytest.mark.parametrize(
    "text, expected",
    [
        ("sk 532", "SK532"),  # space and lower case
        ("SK-532", "SK532"),  # dash
        (" D83209 ", "D83209"),
        ("ba778b", "BA778B"),
    ],
)
def test_parse_flight_id_cleans_the_input(text, expected):
    assert parse_flight_id(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "",
        "A",  # too short
        "SK1' or airport eq 'GOT",  # tries to change the OData filter
        "SK_1",  # not a letter or digit
        "ÅÄ12",  # letters outside A-Z
        "TOOLONG123",  # too long
    ],
)
def test_parse_flight_id_returns_none_for_invalid(text):
    assert parse_flight_id(text) is None
