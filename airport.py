"""FlightInfo terminal app: the menu and the paged flight list."""

import time
from datetime import datetime

import api_client
from api_client import ApiError, build_filter
from config import AIRPORTS, MissingApiKeyError
from destinations import count_destinations, format_destinations, load_city_country
from formatting import (
    SWEDISH_TZ,
    fmt_time,
    get_time_info,
    is_upcoming,
    is_valid_flight,
    print_flight,
    sort_by_time,
)
from user_input import parse_airport, parse_date, parse_flight_id

PAGE_SIZE = 50  # same as the original app
DEMO_AIRPORT = "ARN"
REQUEST_PAUSE = 2  # seconds between requests in a row, to stay under the rate limit (we got a 429 once)

MENU = """
=== Swedavia FlightInfo ===
1. Arrivals
2. Departures
3. Search for a flight number
4. OData query
5. HeartBeat (is the API up?)
6. Demo: all endpoints
7. Destination overview
q. Quit"""


def show_flights(flights, page_size=PAGE_SIZE, ask=input):
    """Print flights page by page: [Enter] next page, [a] show all, [q] back to the menu.

    `ask` is input() by default; tests pass a fake that returns fixed answers.
    """
    total = len(flights)
    if total == 0:
        print("No flights found.")
        return
    shown = 0
    show_all = False
    while shown < total:
        end = total if show_all else min(shown + page_size, total)
        for number, flight in enumerate(flights[shown:end], start=shown + 1):
            print_flight(flight, number)
        shown = end
        print(f"── Showing {shown}/{total} ── ({total - shown} left)")
        if shown == total:
            break
        answer = ask("[Enter] next page | [a] show all | [q] back to menu: ").strip().lower()
        if answer == "q":
            break
        if answer == "a":
            show_all = True


def ask_airport(ask=input):
    """Show the airports and ask until the user gives a valid one. Returns the IATA code."""
    print("Airports: " + ", ".join(f"{code} ({name})" for code, name in AIRPORTS.items()))
    while True:
        code = parse_airport(ask("Enter IATA code or city name (e.g. ARN or Visby): "))
        if code:
            return code
        print("⚠ Unknown airport, try again.")


def ask_date(ask=input):
    """Ask until the user gives a valid date. Returns (date, upcoming_only)."""
    while True:
        result = parse_date(ask("Enter date (YYYY-MM-DD / now / today / tomorrow / yesterday): "))
        if result:
            return result
        print("⚠ Invalid date, try again.")


def prepare_flights(flights, upcoming_only):
    """Keep real flights (and only upcoming ones if asked), sorted by time."""
    flights = [flight for flight in flights if is_valid_flight(flight)]
    if upcoming_only:
        flights = [flight for flight in flights if is_upcoming(flight)]
    return sort_by_time(flights)


def show_airport_flights(fetch, ask=input):
    """Ask for airport and date, fetch the flights with `fetch` and show them."""
    airport = ask_airport(ask)
    day, upcoming_only = ask_date(ask)
    show_flights(prepare_flights(fetch(airport, day), upcoming_only), ask=ask)


def arrivals(ask=input):
    show_airport_flights(api_client.get_arrivals, ask)


def departures(ask=input):
    show_airport_flights(api_client.get_departures, ask)


def ask_flight_id(ask=input):
    """Ask until the user gives a valid flight number. Returns e.g. "SK532"."""
    while True:
        flight_id = parse_flight_id(ask("Enter flight number (e.g. SK532): "))
        if flight_id:
            return flight_id
        print("⚠ Invalid flight number (letters and digits only), try again.")


def search_flight(ask=input):
    """Option 3: find one flight number at an airport on a date (arrivals and departures)."""
    flight_id = ask_flight_id(ask)
    airport = ask_airport(ask)
    day, upcoming_only = ask_date(ask)
    flights = api_client.query(build_filter(airport, day, flight_id=flight_id))
    show_flights(prepare_flights(flights, upcoming_only), ask=ask)


def odata_query(ask=input):
    """Option 4: run a filter the user writes, e.g. airport eq 'ARN' and flightType eq 'D'."""
    print("Fields: airport, flightType ('A'/'D'), scheduled ('YYMMDD'), flightId. Operators: eq, and, or.")
    print("Example: airport eq 'ARN' and flightType eq 'D' and scheduled eq '260929'")
    filter_text = ask("Filter: ").strip()
    if not filter_text:
        print("⚠ No filter given.")
        return
    show_flights(prepare_flights(api_client.query(filter_text), upcoming_only=False), ask=ask)


def heartbeat_check(ask=input):
    """Option 5: check if the API is up."""
    if api_client.heartbeat():
        print("✅ The API is up (IsAlive).")
    else:
        print("⚠ The API answered, but not with IsAlive.")


def summarize(flights):
    """Short text about a list of flights, e.g. "327 flights, first: SK1 (04:50 UTC → 06:50 CEST)"."""
    flights = sort_by_time([flight for flight in flights if is_valid_flight(flight)])
    if not flights:
        return "0 flights"
    first = flights[0]
    first_time = fmt_time(get_time_info(first).get("scheduledUtc"))
    return f"{len(flights)} flights, first: {first.get('flightId')} ({first_time})"


def demo(ask=input, wait=time.sleep):
    """Option 6: call all four endpoints with example values and show one short line for each."""
    today = datetime.now(SWEDISH_TZ).date()
    filter_text = build_filter(DEMO_AIRPORT, today, flight_type="D")
    steps = [
        ("GET /heartBeat",
         lambda: "IsAlive" if api_client.heartbeat() else "answered, but not IsAlive"),
        (f"GET /{DEMO_AIRPORT}/arrivals/{today}",
         lambda: summarize(api_client.get_arrivals(DEMO_AIRPORT, today))),
        (f"GET /{DEMO_AIRPORT}/departures/{today}",
         lambda: summarize(api_client.get_departures(DEMO_AIRPORT, today))),
        (f"GET /query?filter={filter_text}",
         lambda: summarize(api_client.query(filter_text))),
    ]
    for number, (title, run) in enumerate(steps, start=1):
        if number > 1:
            wait(REQUEST_PAUSE)
        print(f"[{number}/{len(steps)}] {title}")
        try:
            print(f"  ✅ {run()}")
        except (ApiError, MissingApiKeyError) as error:
            print(f"  ⚠ {error}")


def ask_direction(ask=input):
    """Ask until the user types 1, 2 or 3, like the original. Returns the choice."""
    while True:
        choice = ask("Show [1] departures, [2] arrivals or [3] both: ").strip()
        if choice in ("1", "2", "3"):
            return choice
        print("Type 1, 2 or 3.")


def destination_overview(ask=input, wait=time.sleep):
    """Option 7: cities with country and number of flights, e.g. "Frankfurt (5 flights) [Germany]"."""
    airport = ask_airport(ask)
    day, upcoming_only = ask_date(ask)
    text_filter = ask("Filter by country or city (Enter = no filter): ")
    choice = ask_direction(ask)
    flights = []
    if choice in ("1", "3"):
        flights += api_client.get_departures(airport, day)
    if choice == "3":
        wait(REQUEST_PAUSE)  # two requests in a row: pause for the rate limit
    if choice in ("2", "3"):
        flights += api_client.get_arrivals(airport, day)
    counts = count_destinations(prepare_flights(flights, upcoming_only))
    lines = format_destinations(counts, load_city_country(), text_filter)
    print(f"\nDestinations for {airport} on {day}:")
    for line in lines:
        print(f"  {line}")
    if not lines:
        print("  No destinations found.")


# Menu choice -> function. New options are added here.
ACTIONS = {
    "1": arrivals,
    "2": departures,
    "3": search_flight,
    "4": odata_query,
    "5": heartbeat_check,
    "6": demo,
    "7": destination_overview,
}


def main(ask=input):
    """Show the menu until the user chooses q. Errors are shown as messages, never as a crash."""
    while True:
        print(MENU)
        choice = ask("Choose: ").strip().lower()
        if choice == "q":
            print("Goodbye!")
            return
        action = ACTIONS.get(choice)
        if action is None:
            print("⚠ Unknown choice, try again.")
            continue
        try:
            action(ask)
        except (ApiError, MissingApiKeyError) as error:
            print(f"⚠ {error}")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
