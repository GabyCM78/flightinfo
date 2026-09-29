"""Tests for destinations.py. Pure logic plus the saved mock data, no API calls."""

import json
from pathlib import Path

import pytest

from destinations import (
    UNKNOWN_COUNTRY,
    city_name,
    count_destinations,
    format_destinations,
    load_city_country,
)
from formatting import is_valid_flight

DEPARTURES_FILE = Path(__file__).parent.parent / "mock_data" / "departures_sample.json"


@pytest.fixture
def departure_flights():
    """All flights from the saved ARN departures response (2026-09-29)."""
    with open(DEPARTURES_FILE, encoding="utf-8-sig") as file:
        return json.load(file)["flights"]


# --- city_name --------------------------------------------------------------

@pytest.mark.parametrize(
    "airport_name, expected",
    [
        ("London LHR", "London"),  # airport code removed
        ("Paris CDG", "Paris"),
        ("Frankfurt", "Frankfurt"),  # no code: unchanged
        ("Åre Östersund", "Åre Östersund"),  # two words, but no code
    ],
)
def test_city_name(airport_name, expected):
    assert city_name(airport_name) == expected


# --- count_destinations -----------------------------------------------------

def test_count_destinations_works_for_both_directions():
    flights = [
        {"arrivalAirportEnglish": "Oslo"},  # a departure going to Oslo
        {"departureAirportEnglish": "Oslo"},  # an arrival coming from Oslo
        {"arrivalAirportEnglish": "Riga"},
    ]
    assert count_destinations(flights) == {"Oslo": 2, "Riga": 1}


def test_count_destinations_joins_airports_of_the_same_city():
    flights = [{"arrivalAirportEnglish": "London LHR"}, {"arrivalAirportEnglish": "London LGW"}]
    assert count_destinations(flights) == {"London": 2}


def test_count_destinations_skips_flights_without_a_name():
    assert count_destinations([{}, {"arrivalAirportEnglish": "Riga"}]) == {"Riga": 1}


# --- format_destinations ----------------------------------------------------

COUNTRIES = {"Oslo": "Norway", "Riga": "Latvia", "Berlin": "Germany", "Munich": "Germany"}


def test_most_flights_first_then_alphabetical():
    counts = {"Riga": 2, "Oslo": 5, "Berlin": 2}
    assert format_destinations(counts, COUNTRIES) == [
        "Oslo (5 flights) [Norway]",
        "Berlin (2 flights) [Germany]",
        "Riga (2 flights) [Latvia]",
    ]


def test_unknown_country():
    assert format_destinations({"Atlantis": 3}, COUNTRIES) == [f"Atlantis (3 flights) [{UNKNOWN_COUNTRY}]"]


def test_one_flight_is_singular():
    assert format_destinations({"Oslo": 1}, COUNTRIES) == ["Oslo (1 flight) [Norway]"]


def test_filter_by_country():
    counts = {"Oslo": 5, "Berlin": 2, "Munich": 1}
    assert format_destinations(counts, COUNTRIES, "germany") == [
        "Berlin (2 flights) [Germany]",
        "Munich (1 flight) [Germany]",
    ]


def test_filter_by_part_of_a_city_name():
    counts = {"Oslo": 5, "Berlin": 2}
    assert format_destinations(counts, COUNTRIES, "  OSL ") == ["Oslo (5 flights) [Norway]"]


# --- real data --------------------------------------------------------------

def test_every_departure_city_has_a_country(departure_flights):
    city_country = load_city_country()
    unknown = [city for city in count_destinations(departure_flights) if city not in city_country]
    assert unknown == []


def test_top_destinations_from_arn(departure_flights):
    # Remove ghost entries first, like the app does (prepare_flights).
    valid = [flight for flight in departure_flights if is_valid_flight(flight)]
    lines = format_destinations(count_destinations(valid), load_city_country())
    assert lines[:4] == [
        "Helsinki (20 flights) [Finland]",
        "Copenhagen (19 flights) [Denmark]",
        "Oslo (15 flights) [Norway]",
        "London (12 flights) [United Kingdom]",
    ]
