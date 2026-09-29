"""Tests for airport.py. input() is replaced by a fake, so no typing is needed."""

import airport
from airport import ask_airport, ask_date, main, prepare_flights, show_flights
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
