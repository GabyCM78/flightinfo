"""Tests for user_input.py. Pure logic, no API calls."""

import pytest

from user_input import parse_airport


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
