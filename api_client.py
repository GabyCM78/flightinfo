"""Talks to the Swedavia FlightInfo API. Every failure becomes an ApiError with a clear message."""

import requests

from config import BASE_URL, TIMEOUT, get_api_key


class ApiError(Exception):
    """Raised when a call to the API fails. The message is safe to show to the user."""


# Clear messages for the HTTP status codes we expect.
STATUS_MESSAGES = {
    400: "The API did not accept the request (400). Check the airport code and date.",
    401: "The API key was rejected (401). Check SWEDAVIA_API_KEY in .env.",
    403: "Access denied (403). Check that your key is subscribed to FlightInfo.",
    404: "Nothing found (404). Check the airport code and date.",
    429: "Too many requests (429). Wait a moment and try again.",
}


def get(path, params=None):
    """GET BASE_URL + path and return the JSON data. Raises ApiError on any failure."""
    headers = {
        "Ocp-Apim-Subscription-Key": get_api_key(),
        "Accept": "application/json",
    }
    try:
        response = requests.get(BASE_URL + path, headers=headers, params=params, timeout=TIMEOUT)
    except requests.Timeout:
        raise ApiError(f"The API did not answer within {TIMEOUT} seconds. Try again later.")
    except requests.ConnectionError:
        raise ApiError("Could not connect to the API. Check your internet connection.")
    except requests.RequestException as error:
        raise ApiError(f"The request failed ({type(error).__name__}).")

    if response.status_code != 200:
        message = STATUS_MESSAGES.get(
            response.status_code, f"The API answered with an error ({response.status_code})."
        )
        raise ApiError(message)

    try:
        return response.json()
    except ValueError:
        raise ApiError("The API answered, but not with valid JSON.")


def heartbeat():
    """Return True if the API answers "IsAlive"."""
    return get("/heartBeat") == "IsAlive"


def _get_flights(direction, iata, day):
    """Fetch "arrivals" or "departures" for one airport and one day (UTC). Returns a list."""
    data = get(f"/{iata.upper()}/{direction}/{day.isoformat()}")
    if not isinstance(data, dict):
        raise ApiError("The API answered with unexpected data.")
    return data.get("flights") or []


def get_arrivals(iata, day):
    """Return all arrivals at an airport on a date (a datetime.date, in UTC)."""
    return _get_flights("arrivals", iata, day)


def get_departures(iata, day):
    """Return all departures from an airport on a date (a datetime.date, in UTC)."""
    return _get_flights("departures", iata, day)


# Safety limit, so one query never uses too many API requests (the original had the same idea).
MAX_PAGES = 5


def unwrap_flight(item):
    """Return the flight inside a /query item ({"arrival": {...}} or {"departure": {...}}), or None."""
    if not isinstance(item, dict):
        return None
    return item.get("arrival") or item.get("departure")


def query(filter_text, count=1000, max_pages=MAX_PAGES):
    """Run an OData query and return the unwrapped flights from up to max_pages pages.

    The API sends a continuationtoken even on the last page, so we also stop
    when a page has fewer flights than we asked for.
    """
    params = {"filter": filter_text, "count": count}
    flights = []
    for _ in range(max_pages):
        data = get("/query", params=params)
        if not isinstance(data, dict):
            raise ApiError("The API answered with unexpected data.")
        page = data.get("flights") or []
        for item in page:
            flight = unwrap_flight(item)
            if flight:
                flights.append(flight)
        token = data.get("continuationtoken")
        if not token or len(page) < count:
            break
        params["continuationtoken"] = token
    return flights
