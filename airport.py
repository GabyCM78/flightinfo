"""FlightInfo terminal app: the menu and the paged flight list."""

import api_client
from api_client import ApiError
from config import AIRPORTS, MissingApiKeyError
from formatting import is_upcoming, is_valid_flight, print_flight, sort_by_time
from user_input import parse_airport, parse_date

PAGE_SIZE = 50  # same as the original app

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


# Menu choice -> function. New options are added here.
ACTIONS = {
    "1": arrivals,
    "2": departures,
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
