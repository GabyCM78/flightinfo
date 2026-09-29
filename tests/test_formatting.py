"""Tests for formatting.py. They use mock data only, never the real API."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from formatting import (
    MISSING,
    fmt_time,
    format_flight,
    is_upcoming,
    is_valid_flight,
    print_flight,
)

MOCK_DIR = Path(__file__).parent.parent / "mock_data"
ARRIVALS_FILE = MOCK_DIR / "arrivals_sample.json"
DEPARTURES_FILE = MOCK_DIR / "departures_sample.json"

# A fixed "now", so the is_upcoming tests give the same result every time.
NOON_UTC = datetime(2026, 9, 28, 12, tzinfo=timezone.utc)


@pytest.fixture
def mock_flights():
    """All flights from the saved ARN arrivals response (2026-09-28)."""
    with open(ARRIVALS_FILE, encoding="utf-8-sig") as file:
        return json.load(file)["flights"]


@pytest.fixture
def departure_flights():
    """All flights from the saved ARN departures response (2026-09-29)."""
    with open(DEPARTURES_FILE, encoding="utf-8-sig") as file:
        return json.load(file)["flights"]


def make_flight(status="SCH", **times):
    """Build a small arrival for tests, e.g. make_flight(scheduledUtc="...")."""
    return {
        "flightId": "SK1",
        "arrivalTime": times,
        "locationAndStatus": {"flightLegStatus": status},
    }


# --- fmt_time ---------------------------------------------------------------

@pytest.mark.parametrize(
    "utc_text, expected",
    [
        ("2026-09-28T20:25:00Z", "20:25 UTC → 22:25 CEST"),  # summer time
        ("2026-01-15T16:25:00Z", "16:25 UTC → 17:25 CET"),  # winter time, as in the original video
        ("2026-09-27T22:00:00Z", "22:00 UTC → 00:00 CEST"),  # past midnight in Sweden
        ("2026-09-27T21:39:08Z", "21:39 UTC → 23:39 CEST"),  # seconds are dropped
        ("2026-10-25T00:30:00Z", "00:30 UTC → 02:30 CEST"),  # clock change day, before 01:00 UTC
        ("2026-10-25T01:30:00Z", "01:30 UTC → 02:30 CET"),  # clock change day, after 01:00 UTC
    ],
)
def test_fmt_time_converts_utc_to_swedish_time(utc_text, expected):
    assert fmt_time(utc_text) == expected


@pytest.mark.parametrize("bad_value", [None, "", "N/A", "not a time", 123])
def test_fmt_time_returns_missing_for_bad_input(bad_value):
    assert fmt_time(bad_value) == MISSING


# --- is_valid_flight --------------------------------------------------------

def test_valid_flight_is_accepted():
    assert is_valid_flight(make_flight(scheduledUtc="2026-09-28T10:00:00Z"))


def test_cancelled_flight_is_kept():
    assert is_valid_flight(make_flight(status="CAN", scheduledUtc="2026-09-28T10:00:00Z"))


def test_deleted_flight_is_skipped():
    assert not is_valid_flight(make_flight(status="DEL", scheduledUtc="2026-09-28T10:00:00Z"))


def test_flight_without_id_is_skipped():
    flight = make_flight(scheduledUtc="2026-09-28T10:00:00Z")
    del flight["flightId"]
    assert not is_valid_flight(flight)


def test_flight_without_scheduled_time_is_skipped():
    assert not is_valid_flight(make_flight())


@pytest.mark.parametrize("not_a_flight", [None, "SK1", 42, []])
def test_non_dict_is_skipped(not_a_flight):
    assert not is_valid_flight(not_a_flight)


def test_departure_is_accepted():
    flight = {"flightId": "SK2", "departureTime": {"scheduledUtc": "2026-09-28T10:00:00Z"}}
    assert is_valid_flight(flight)


def test_mock_data_has_327_valid_flights(mock_flights):
    valid = [flight for flight in mock_flights if is_valid_flight(flight)]
    assert len(mock_flights) == 365
    assert len(valid) == 327  # 38 ghost entries (DEL) are removed


# --- is_upcoming ------------------------------------------------------------

@pytest.mark.parametrize(
    "times, expected",
    [
        ({"scheduledUtc": "2026-09-28T15:00:00Z"}, True),  # later than now
        ({"scheduledUtc": "2026-09-28T09:00:00Z"}, False),  # already passed
        ({"scheduledUtc": "2026-09-28T12:00:00Z"}, True),  # exactly now counts as upcoming
        ({"scheduledUtc": "2026-09-28T09:00:00Z", "estimatedUtc": "2026-09-28T13:00:00Z"}, True),  # delayed
        ({"scheduledUtc": "2026-09-28T15:00:00Z", "actualUtc": "2026-09-28T11:50:00Z"}, False),  # landed early
        ({}, False),  # no times at all
        ({"scheduledUtc": "N/A"}, False),  # broken time
    ],
)
def test_is_upcoming(times, expected):
    assert is_upcoming(make_flight(**times), now=NOON_UTC) is expected


def test_is_upcoming_uses_current_time_by_default():
    assert is_upcoming(make_flight(scheduledUtc="2100-01-01T00:00:00Z"))
    assert not is_upcoming(make_flight(scheduledUtc="2000-01-01T00:00:00Z"))


def test_is_upcoming_rejects_non_dict():
    assert not is_upcoming(None, now=NOON_UTC)


def test_mock_data_has_146_upcoming_flights_at_noon(mock_flights):
    valid = [flight for flight in mock_flights if is_valid_flight(flight)]
    upcoming = [flight for flight in valid if is_upcoming(flight, now=NOON_UTC)]
    assert len(upcoming) == 146


# --- format_flight / print_flight -------------------------------------------

def test_format_flight_with_all_fields(mock_flights):
    flight = next(f for f in mock_flights if f["flightId"] == "JTD664")
    text = format_flight(flight, 1)
    assert "[1] → JTD664 | Jettime (JTD)" in text
    assert "From : Lemnos" in text
    assert "Terminal : T5   Gate: C41" in text
    assert "Baggage  : 3" in text
    assert "Actual: 21:39 UTC → 23:39 CEST" in text


def test_format_flight_with_empty_flight_does_not_crash():
    text = format_flight({}, 7)
    assert "[7] → – | – (–)" in text
    assert "Gate: –" in text
    assert "Sched : –" in text


def test_format_flight_falls_back_to_iata_code():
    flight = {"flightLegIdentifier": {"departureAirportIata": "LHR", "arrivalAirportIata": "ARN"}}
    text = format_flight(flight, 1)
    assert "From : LHR" in text
    assert "To   : ARN" in text


def test_print_flight_prints_the_formatted_text(capsys):
    flight = make_flight(scheduledUtc="2026-09-28T20:25:00Z")
    print_flight(flight, 3)
    printed = capsys.readouterr().out
    assert printed == format_flight(flight, 3) + "\n"


# --- departures (real data) -------------------------------------------------

def test_departures_mock_has_299_valid_flights(departure_flights):
    valid = [flight for flight in departure_flights if is_valid_flight(flight)]
    assert len(departure_flights) == 342
    assert len(valid) == 299  # 43 ghost entries (DEL) are removed


def test_departed_flights_are_not_upcoming(departure_flights):
    departed = [
        flight for flight in departure_flights
        if flight["locationAndStatus"]["flightLegStatus"] == "ACT"
    ]
    assert len(departed) == 146
    assert not any(is_upcoming(flight, now=NOON_UTC) for flight in departed)


def test_format_departure_uses_arrival_airport_as_to(departure_flights):
    flight = next(f for f in departure_flights if is_valid_flight(f))
    text = format_flight(flight, 1)
    assert "From : ARN" in text
    assert f"To   : {flight['arrivalAirportEnglish']}" in text


def test_format_departure_has_no_baggage(departure_flights):
    flight = next(f for f in departure_flights if is_valid_flight(f))
    assert "Baggage  : –" in format_flight(flight, 1)
