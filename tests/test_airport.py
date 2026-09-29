"""Tests for airport.py. input() is replaced by a fake, so no typing is needed."""

import pytest

import airport
from airport import (
    ask_airport,
    ask_date,
    ask_direction,
    demo,
    destination_overview,
    heartbeat_check,
    main,
    odata_query,
    prepare_flights,
    search_flight,
    show_flights,
    summarize,
)
from api_client import ApiError
from config import MissingApiKeyError


def make_flights(count):
    """A list of small flights: SK1, SK2, ..."""
    return [{"flightId": f"SK{i}"} for i in range(1, count + 1)]


def fake_ask(answers):
    """A fake input(): returns the answers in order and records every prompt."""
    prompts = []
    replies = iter(answers)

    def ask(prompt):
        prompts.append(prompt)
        return next(replies)

    return ask, prompts


# --- show_flights -----------------------------------------------------------

def test_empty_list_says_no_flights(capsys):
    ask, prompts = fake_ask([])
    show_flights([], ask=ask)
    assert "No flights found." in capsys.readouterr().out
    assert prompts == []


def test_less_than_one_page_shows_all_without_asking(capsys):
    ask, prompts = fake_ask([])
    show_flights(make_flights(3), page_size=5, ask=ask)
    out = capsys.readouterr().out
    assert "[3] → SK3" in out
    assert "── Showing 3/3 ── (0 left)" in out
    assert prompts == []


def test_enter_shows_next_page_and_numbering_continues(capsys):
    ask, prompts = fake_ask([""])
    show_flights(make_flights(3), page_size=2, ask=ask)
    assert "[3] → SK3" in capsys.readouterr().out
    assert len(prompts) == 1


def test_q_stops_before_next_page(capsys):
    ask, _ = fake_ask(["q"])
    show_flights(make_flights(3), page_size=2, ask=ask)
    out = capsys.readouterr().out
    assert "[2] → SK2" in out
    assert "[3] → SK3" not in out


def test_a_shows_all_remaining_at_once(capsys):
    ask, prompts = fake_ask(["a"])
    show_flights(make_flights(5), page_size=2, ask=ask)
    out = capsys.readouterr().out
    assert "[5] → SK5" in out
    assert "── Showing 5/5 ── (0 left)" in out
    assert len(prompts) == 1


def test_unknown_answer_works_like_enter(capsys):
    ask, _ = fake_ask(["x"])
    show_flights(make_flights(3), page_size=2, ask=ask)
    assert "[3] → SK3" in capsys.readouterr().out


def test_counter_line(capsys):
    ask, _ = fake_ask(["q"])
    show_flights(make_flights(5), page_size=2, ask=ask)
    assert "── Showing 2/5 ── (3 left)" in capsys.readouterr().out


# --- ask_airport / ask_date -------------------------------------------------

def test_ask_airport_asks_again_until_valid(capsys):
    ask, prompts = fake_ask(["XXX", "visby"])
    assert ask_airport(ask) == "VBY"
    assert capsys.readouterr().out.count("Unknown airport") == 1
    assert len(prompts) == 2


def test_ask_date_asks_again_until_valid(capsys):
    ask, prompts = fake_ask(["29/9", "2026-09-29"])
    day, upcoming_only = ask_date(ask)
    assert day.isoformat() == "2026-09-29"
    assert upcoming_only is False
    assert capsys.readouterr().out.count("Invalid date") == 1


# --- prepare_flights --------------------------------------------------------

def flight(flight_id, scheduled, status="SCH"):
    """A small arrival with a scheduled time and a status."""
    return {
        "flightId": flight_id,
        "arrivalTime": {"scheduledUtc": scheduled},
        "locationAndStatus": {"flightLegStatus": status},
    }


def test_prepare_flights_removes_ghosts_and_sorts():
    flights = [
        flight("LATE", "2026-09-28T20:00:00Z"),
        flight("GHOST", "2026-09-28T10:00:00Z", status="DEL"),
        flight("EARLY", "2026-09-28T06:00:00Z"),
    ]
    result = prepare_flights(flights, upcoming_only=False)
    assert [f["flightId"] for f in result] == ["EARLY", "LATE"]


def test_prepare_flights_upcoming_only_removes_past_flights():
    flights = [flight("PAST", "2000-01-01T00:00:00Z"), flight("FUTURE", "2100-01-01T00:00:00Z")]
    result = prepare_flights(flights, upcoming_only=True)
    assert [f["flightId"] for f in result] == ["FUTURE"]


# --- main -------------------------------------------------------------------

def test_main_q_says_goodbye(capsys):
    ask, _ = fake_ask(["q"])
    main(ask)
    assert "Goodbye!" in capsys.readouterr().out


def test_main_unknown_choice_asks_again(capsys):
    ask, _ = fake_ask(["9", "q"])
    main(ask)
    out = capsys.readouterr().out
    assert "Unknown choice" in out
    assert "Goodbye!" in out


def test_main_arrivals_shows_flights(monkeypatch, capsys):
    monkeypatch.setattr(
        airport.api_client, "get_arrivals", lambda code, day: [flight("SK1", "2026-09-29T10:00:00Z")]
    )
    ask, _ = fake_ask(["1", "ARN", "2026-09-29", "q"])
    main(ask)
    assert "[1] → SK1" in capsys.readouterr().out


def test_main_shows_api_error_and_keeps_running(monkeypatch, capsys):
    def broken_fetch(code, day):
        raise ApiError("The API key was rejected (401).")

    monkeypatch.setattr(airport.api_client, "get_arrivals", broken_fetch)
    ask, _ = fake_ask(["1", "ARN", "today", "q"])
    main(ask)
    out = capsys.readouterr().out
    assert "⚠ The API key was rejected (401)." in out
    assert "Goodbye!" in out  # the menu came back, no crash


def test_main_shows_missing_key_error(monkeypatch, capsys):
    def no_key(code, day):
        raise MissingApiKeyError("SWEDAVIA_API_KEY is missing.")

    monkeypatch.setattr(airport.api_client, "get_departures", no_key)
    ask, _ = fake_ask(["2", "GOT", "today", "q"])
    main(ask)
    assert "⚠ SWEDAVIA_API_KEY is missing." in capsys.readouterr().out


# --- options 3, 4 and 5 -----------------------------------------------------

def use_fake_query(monkeypatch, flights=()):
    """Replace api_client.query. Returns a list with every filter it was called with."""
    filters = []

    def fake_query(filter_text):
        filters.append(filter_text)
        return list(flights)

    monkeypatch.setattr(airport.api_client, "query", fake_query)
    return filters


def test_search_flight_builds_the_filter(monkeypatch):
    filters = use_fake_query(monkeypatch)
    ask, _ = fake_ask(["sk 532", "ARN", "2026-09-29"])
    search_flight(ask)
    assert filters == ["airport eq 'ARN' and scheduled eq '260929' and flightId eq 'SK532'"]


def test_search_flight_asks_again_for_invalid_flight_id(monkeypatch, capsys):
    use_fake_query(monkeypatch)
    ask, _ = fake_ask(["SK1' or airport eq 'GOT", "SK1", "ARN", "2026-09-29"])
    search_flight(ask)
    assert capsys.readouterr().out.count("Invalid flight number") == 1


def test_odata_query_sends_the_filter_unchanged(monkeypatch, capsys):
    filters = use_fake_query(monkeypatch, [flight("SK1", "2026-09-29T10:00:00Z")])
    ask, _ = fake_ask(["airport eq 'VBY' and flightType eq 'A'"])
    odata_query(ask)
    assert filters == ["airport eq 'VBY' and flightType eq 'A'"]
    assert "[1] → SK1" in capsys.readouterr().out


def test_odata_query_empty_filter_makes_no_call(monkeypatch, capsys):
    filters = use_fake_query(monkeypatch)
    ask, _ = fake_ask(["   "])
    odata_query(ask)
    assert filters == []
    assert "No filter given" in capsys.readouterr().out


def test_heartbeat_check_up(monkeypatch, capsys):
    monkeypatch.setattr(airport.api_client, "heartbeat", lambda: True)
    heartbeat_check()
    assert "✅ The API is up" in capsys.readouterr().out


def test_heartbeat_check_not_alive(monkeypatch, capsys):
    monkeypatch.setattr(airport.api_client, "heartbeat", lambda: False)
    heartbeat_check()
    assert "not with IsAlive" in capsys.readouterr().out


# --- option 6: demo ---------------------------------------------------------

def test_summarize_empty_list():
    assert summarize([]) == "0 flights"


def test_summarize_skips_ghosts_and_shows_the_earliest_flight():
    flights = [
        flight("LATE", "2026-09-29T20:00:00Z"),
        flight("GHOST", "2026-09-29T01:00:00Z", status="DEL"),
        flight("EARLY", "2026-09-29T06:00:00Z"),
    ]
    assert summarize(flights) == "2 flights, first: EARLY (06:00 UTC → 08:00 CEST)"


def use_fake_endpoints(monkeypatch, arrivals_error=None):
    """Replace all four API functions. If arrivals_error is given, get_arrivals raises it."""
    def fake_arrivals(code, day):
        if arrivals_error:
            raise arrivals_error
        return [flight("SK1", "2026-09-29T10:00:00Z")]

    monkeypatch.setattr(airport.api_client, "heartbeat", lambda: True)
    monkeypatch.setattr(airport.api_client, "get_arrivals", fake_arrivals)
    monkeypatch.setattr(airport.api_client, "get_departures", lambda code, day: [])
    monkeypatch.setattr(airport.api_client, "query", lambda filter_text: [])


def test_demo_runs_all_four_steps(monkeypatch, capsys):
    use_fake_endpoints(monkeypatch)
    demo(wait=lambda seconds: None)
    out = capsys.readouterr().out
    assert out.count("✅") == 4
    assert "✅ IsAlive" in out
    assert "[4/4] GET /query" in out


def test_demo_keeps_going_after_an_error(monkeypatch, capsys):
    use_fake_endpoints(monkeypatch, arrivals_error=ApiError("Too many requests (429)."))
    demo(wait=lambda seconds: None)
    out = capsys.readouterr().out
    assert "⚠ Too many requests (429)." in out
    assert out.count("✅") == 3  # steps 1, 3 and 4 still ran


def test_demo_pauses_between_requests(monkeypatch):
    use_fake_endpoints(monkeypatch)
    pauses = []
    demo(wait=pauses.append)
    assert pauses == [airport.REQUEST_PAUSE] * 3


# --- option 7: destination overview -----------------------------------------

def departure_to(city, status="SCH"):
    """A small departure going to `city`."""
    return {
        "flightId": "D1",
        "departureTime": {"scheduledUtc": "2026-09-29T10:00:00Z"},
        "arrivalAirportEnglish": city,
        "locationAndStatus": {"flightLegStatus": status},
    }


def arrival_from(city):
    """A small arrival coming from `city`."""
    return {
        "flightId": "A1",
        "arrivalTime": {"scheduledUtc": "2026-09-29T10:00:00Z"},
        "departureAirportEnglish": city,
        "locationAndStatus": {"flightLegStatus": "SCH"},
    }


def use_fake_directions(monkeypatch, departures=(), arrivals=()):
    """Replace get_departures and get_arrivals. Returns a list of which ones were called."""
    called = []

    def fake_departures(code, day):
        called.append("departures")
        return list(departures)

    def fake_arrivals(code, day):
        called.append("arrivals")
        return list(arrivals)

    monkeypatch.setattr(airport.api_client, "get_departures", fake_departures)
    monkeypatch.setattr(airport.api_client, "get_arrivals", fake_arrivals)
    return called


def test_ask_direction_asks_again_until_1_2_or_3(capsys):
    ask, _ = fake_ask(["4", "2"])
    assert ask_direction(ask) == "2"
    assert capsys.readouterr().out.count("Type 1, 2 or 3.") == 1


@pytest.mark.parametrize(
    "choice, expected_calls",
    [("1", ["departures"]), ("2", ["arrivals"]), ("3", ["departures", "arrivals"])],
)
def test_destination_overview_calls_the_right_endpoints(monkeypatch, choice, expected_calls):
    called = use_fake_directions(monkeypatch)
    ask, _ = fake_ask(["ARN", "today", "", choice])
    destination_overview(ask, wait=lambda seconds: None)
    assert called == expected_calls


def test_destination_overview_both_pauses_once(monkeypatch):
    use_fake_directions(monkeypatch)
    pauses = []
    ask, _ = fake_ask(["ARN", "today", "", "3"])
    destination_overview(ask, wait=pauses.append)
    assert pauses == [airport.REQUEST_PAUSE]


def test_destination_overview_counts_and_skips_ghosts(monkeypatch, capsys):
    use_fake_directions(
        monkeypatch,
        departures=[departure_to("Oslo"), departure_to("Oslo"), departure_to("Riga", status="DEL")],
        arrivals=[arrival_from("Oslo")],
    )
    ask, _ = fake_ask(["ARN", "today", "", "3"])
    destination_overview(ask, wait=lambda seconds: None)
    out = capsys.readouterr().out
    assert "Oslo (3 flights) [Norway]" in out
    assert "Riga" not in out  # the only Riga flight was a ghost entry


def test_destination_overview_filter_and_empty_result(monkeypatch, capsys):
    use_fake_directions(monkeypatch, departures=[departure_to("Oslo")])
    ask, _ = fake_ask(["ARN", "today", "germany", "1"])
    destination_overview(ask, wait=lambda seconds: None)
    assert "No destinations found." in capsys.readouterr().out
