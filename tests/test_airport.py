"""Tests for airport.py. input() is replaced by a fake, so no typing is needed."""

from airport import show_flights


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
