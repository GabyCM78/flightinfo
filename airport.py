"""FlightInfo terminal app: the menu and the paged flight list."""

from formatting import print_flight

PAGE_SIZE = 50  # same as the original app


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
