"""Tests for api_client.py. requests.get is replaced, so no real API calls are made."""

from datetime import date

import pytest
import requests

import api_client
from api_client import ApiError, get, get_arrivals, get_departures, heartbeat, query, unwrap_flight
from config import BASE_URL, TIMEOUT, MissingApiKeyError

DAY = date(2026, 9, 29)


class FakeResponse:
    """Stands in for a requests.Response: a status code and a JSON body."""

    def __init__(self, status_code=200, data=None, bad_json=False):
        self.status_code = status_code
        self._data = data
        self._bad_json = bad_json

    def json(self):
        if self._bad_json:
            raise ValueError("not JSON")
        return self._data


@pytest.fixture(autouse=True)
def fake_key(monkeypatch):
    """Use a fake API key in every test, never the real one from .env."""
    monkeypatch.setenv("SWEDAVIA_API_KEY", "test-key")


def use_fake_get(monkeypatch, response=None, error=None):
    """Replace requests.get. Returns a dict that records how it was called."""
    calls = {}

    def fake_get(url, **kwargs):
        calls["url"] = url
        calls.update(kwargs)  # headers, params, timeout
        if error:
            raise error
        return response

    monkeypatch.setattr(api_client.requests, "get", fake_get)
    return calls


# --- successful calls -------------------------------------------------------

def test_get_returns_json_data(monkeypatch):
    use_fake_get(monkeypatch, FakeResponse(data={"flights": []}))
    assert get("/ARN/arrivals/2026-09-28") == {"flights": []}


def test_get_builds_the_full_url(monkeypatch):
    calls = use_fake_get(monkeypatch, FakeResponse(data="IsAlive"))
    get("/heartBeat")
    assert calls["url"] == BASE_URL + "/heartBeat"


def test_get_sends_key_and_accept_headers(monkeypatch):
    calls = use_fake_get(monkeypatch, FakeResponse(data="IsAlive"))
    get("/heartBeat")
    assert calls["headers"]["Ocp-Apim-Subscription-Key"] == "test-key"
    assert calls["headers"]["Accept"] == "application/json"


def test_get_always_uses_a_timeout(monkeypatch):
    calls = use_fake_get(monkeypatch, FakeResponse(data="IsAlive"))
    get("/heartBeat")
    assert calls["timeout"] == TIMEOUT


def test_get_passes_query_params(monkeypatch):
    calls = use_fake_get(monkeypatch, FakeResponse(data={}))
    get("/query", params={"filter": "x", "count": 50})
    assert calls["params"] == {"filter": "x", "count": 50}


# --- HTTP errors ------------------------------------------------------------

@pytest.mark.parametrize("status_code", [400, 401, 403, 404, 429])
def test_known_http_errors_give_a_clear_message(monkeypatch, status_code):
    use_fake_get(monkeypatch, FakeResponse(status_code=status_code))
    with pytest.raises(ApiError) as error_info:
        get("/heartBeat")
    assert str(error_info.value) == api_client.STATUS_MESSAGES[status_code]


def test_unknown_http_error_gives_a_general_message(monkeypatch):
    use_fake_get(monkeypatch, FakeResponse(status_code=500))
    with pytest.raises(ApiError, match="error \\(500\\)"):
        get("/heartBeat")


# --- network errors ---------------------------------------------------------

def test_timeout_gives_api_error(monkeypatch):
    use_fake_get(monkeypatch, error=requests.Timeout())
    with pytest.raises(ApiError, match="did not answer"):
        get("/heartBeat")


def test_no_network_gives_api_error(monkeypatch):
    use_fake_get(monkeypatch, error=requests.ConnectionError())
    with pytest.raises(ApiError, match="internet connection"):
        get("/heartBeat")


def test_other_request_error_gives_api_error(monkeypatch):
    use_fake_get(monkeypatch, error=requests.TooManyRedirects())
    with pytest.raises(ApiError, match="TooManyRedirects"):
        get("/heartBeat")


# --- bad data ---------------------------------------------------------------

def test_invalid_json_gives_api_error(monkeypatch):
    use_fake_get(monkeypatch, FakeResponse(bad_json=True))
    with pytest.raises(ApiError, match="valid JSON"):
        get("/heartBeat")


# --- security ---------------------------------------------------------------

def test_missing_key_raises_before_any_call(monkeypatch):
    monkeypatch.delenv("SWEDAVIA_API_KEY")
    calls = use_fake_get(monkeypatch, FakeResponse(data="IsAlive"))
    with pytest.raises(MissingApiKeyError):
        get("/heartBeat")
    assert calls == {}  # requests.get was never called


def test_key_is_never_in_the_error_message(monkeypatch):
    use_fake_get(monkeypatch, FakeResponse(status_code=401))
    with pytest.raises(ApiError) as error_info:
        get("/heartBeat")
    assert "test-key" not in str(error_info.value)


# --- heartbeat --------------------------------------------------------------

def test_heartbeat_true_when_alive(monkeypatch):
    use_fake_get(monkeypatch, FakeResponse(data="IsAlive"))
    assert heartbeat() is True


def test_heartbeat_false_for_other_answer(monkeypatch):
    use_fake_get(monkeypatch, FakeResponse(data="Down"))
    assert heartbeat() is False


def test_heartbeat_passes_errors_on(monkeypatch):
    use_fake_get(monkeypatch, FakeResponse(status_code=401))
    with pytest.raises(ApiError, match="401"):
        heartbeat()


# --- get_arrivals / get_departures ------------------------------------------

def test_get_arrivals_uses_the_arrivals_url(monkeypatch):
    calls = use_fake_get(monkeypatch, FakeResponse(data={"flights": []}))
    get_arrivals("ARN", DAY)
    assert calls["url"] == BASE_URL + "/ARN/arrivals/2026-09-29"


def test_get_departures_uses_the_departures_url(monkeypatch):
    calls = use_fake_get(monkeypatch, FakeResponse(data={"flights": []}))
    get_departures("GOT", DAY)
    assert calls["url"] == BASE_URL + "/GOT/departures/2026-09-29"


def test_airport_code_is_made_upper_case(monkeypatch):
    calls = use_fake_get(monkeypatch, FakeResponse(data={"flights": []}))
    get_arrivals("arn", DAY)
    assert "/ARN/" in calls["url"]


def test_get_arrivals_returns_the_list_of_flights(monkeypatch):
    flights = [{"flightId": "SK1"}, {"flightId": "SK2"}]
    use_fake_get(monkeypatch, FakeResponse(data={"numberOfFlights": 2, "flights": flights}))
    assert get_arrivals("ARN", DAY) == flights


def test_missing_flights_gives_empty_list(monkeypatch):
    use_fake_get(monkeypatch, FakeResponse(data={"numberOfFlights": 0}))
    assert get_arrivals("ARN", DAY) == []


def test_unexpected_data_gives_api_error(monkeypatch):
    use_fake_get(monkeypatch, FakeResponse(data="IsAlive"))
    with pytest.raises(ApiError, match="unexpected data"):
        get_departures("ARN", DAY)


# --- query / unwrap_flight --------------------------------------------------

def use_fake_pages(monkeypatch, pages):
    """Replace requests.get with a fake that returns one page per call.

    Returns a list with a copy of the params of every call.
    """
    calls = []
    responses = iter(pages)

    def fake_get(url, **kwargs):
        calls.append(dict(kwargs["params"]))  # a copy, because query() changes params later
        return FakeResponse(data=next(responses))

    monkeypatch.setattr(api_client.requests, "get", fake_get)
    return calls


def arrival(flight_id):
    """A wrapped /query item, as the real API sends it."""
    return {"arrival": {"flightId": flight_id}}


def test_query_single_page_unwraps_and_stops(monkeypatch):
    # The real API sends a token even on the last page.
    calls = use_fake_pages(monkeypatch, [{"flights": [arrival("SK1")], "continuationtoken": "T1"}])
    assert query("x", count=5) == [{"flightId": "SK1"}]
    assert len(calls) == 1


def test_query_follows_the_token_to_page_two(monkeypatch):
    calls = use_fake_pages(monkeypatch, [
        {"flights": [arrival("SK1"), arrival("SK2")], "continuationtoken": "T1"},
        {"flights": [arrival("SK3")], "continuationtoken": "T2"},
    ])
    flights = query("x", count=2)
    assert [f["flightId"] for f in flights] == ["SK1", "SK2", "SK3"]
    assert len(calls) == 2
    assert "continuationtoken" not in calls[0]
    assert calls[1]["continuationtoken"] == "T1"


def test_query_stops_when_token_is_missing(monkeypatch):
    calls = use_fake_pages(monkeypatch, [{"flights": [arrival("SK1"), arrival("SK2")]}])
    assert len(query("x", count=2)) == 2
    assert len(calls) == 1


def test_query_never_uses_more_than_max_pages(monkeypatch):
    full_page = {"flights": [arrival("SK1")], "continuationtoken": "T"}
    calls = use_fake_pages(monkeypatch, [full_page] * 10)
    query("x", count=1, max_pages=3)
    assert len(calls) == 3


def test_query_empty_page_gives_empty_list(monkeypatch):
    calls = use_fake_pages(monkeypatch, [{"flights": [], "continuationtoken": "T"}])
    assert query("x") == []
    assert len(calls) == 1


def test_query_sends_filter_and_count(monkeypatch):
    calls = use_fake_pages(monkeypatch, [{"flights": []}])
    query("airport eq 'ARN'", count=50)
    assert calls[0] == {"filter": "airport eq 'ARN'", "count": 50}


def test_query_unexpected_data_gives_api_error(monkeypatch):
    use_fake_pages(monkeypatch, ["IsAlive"])
    with pytest.raises(ApiError, match="unexpected data"):
        query("x")


@pytest.mark.parametrize(
    "item, expected",
    [
        ({"arrival": {"flightId": "SK1"}}, {"flightId": "SK1"}),
        ({"departure": {"flightId": "SK2"}}, {"flightId": "SK2"}),
        ({"somethingElse": {"flightId": "SK3"}}, None),
        ("not a dict", None),
        (None, None),
    ],
)
def test_unwrap_flight(item, expected):
    assert unwrap_flight(item) == expected
