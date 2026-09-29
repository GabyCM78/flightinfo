# Swedavia FlightInfo – Project Documentation

**Assignment:** Reverse Engineer a Result (APL)
**Result:** a Python terminal app for the Swedavia FlightInfo API v2 – the same features as the original app,
but safer, more stable, tested and better structured.
**Repository:** https://github.com/GabyCM78/flightinfo

---

## Phase 1 – Research

### Goal
I had a video of a finished app, but not its source code. My goal was to understand how it worked by working
backwards from what I could see (the output) to the data and the logic behind it, and then rebuild it – improved.

### Information gathering

**1. The original app (from the video)**
- A **Python terminal app** with a menu: 1 Arrivals, 2 Departures, 3 Search flight number, 4 OData query,
  5 HeartBeat, 6 Demo, q Quit.
- It shows **50 flights per page** with `[Enter] next page | [a] show all | [q] back to menu`.
- It converts times from UTC to Swedish time (`16:25 UTC → 17:25 CET`).
- Airport input: "IATA code or city name (e.g. ARN or Visby)". Date input: `YYYY-MM-DD / now / today / tomorrow / yesterday`.
- The destination overview was a **separate script** that ran once and exited.
- For ARN it showed "Showing 50/220", while the API had about 365 flights that day. The code also had
  `_is_valid_flight` and `_is_upcoming`. So it probably hid some flights.

**Weaknesses I noticed:** the **API key was hardcoded** in the source code (visible in the video),
there were no visible tests, and most of the code was in one large file.

**What the video did not show:** options 3 and 6 were never run in the video, so I based them on the
menu text and documented my assumptions.

**2. The Swedavia API**
- I created a free account on the Swedavia API portal and subscribed to FlightInfo (10,000 requests/month).
- I tested `GET /heartBeat` (answer: the JSON string `"IsAlive"`) and `GET /ARN/arrivals/2026-09-28`
  (365 flights) in the portal, and saved the responses as **mock data** for my tests.
- I read Swedavia's PDF "Using the FlightInfo API" for the `/query` endpoint (OData filter, `count`, `continuationtoken`).

**3. Studying the real data**
Instead of trusting the documentation alone, I studied the saved JSON and later made small, safe test calls.
Important findings:
- **Fields are often missing** (no gate, no estimated time, empty baggage), so every field is read with a default.
- **38 of 365 arrivals were "ghost entries"**: status `DEL` (deleted) with almost no data.
  Cancelled flights have their own status, `CAN`, and are real information for travellers.
- Departures have no baggage belt but check-in desks and gate times, and extra statuses (`ACT` = Departed).
- In `/query`, each flight is **wrapped** (`{"arrival": {...}}`), the paging key is `continuationtoken` with a
  **lower-case t**, and a token is sent **even on the last page**.

### Choice of tools and techniques
| Tool | Why |
|---|---|
| Python 3.14 + virtual environment (`.venv`) | Same language as the original; the venv keeps packages separate |
| `requests` | Simple HTTP calls, with timeouts |
| `python-dotenv` | Reads the API key from `.env`, so it is never in the code |
| `zoneinfo` + `tzdata` | Correct Swedish time, including summer/winter time (Windows needs `tzdata`) |
| `pytest` | Automatic tests; `monkeypatch` replaces the network so no real calls are made |
| Git + GitHub | Version history and backup; a small commit after each step |
| VS Code + Claude | Claude as a coding assistant that explained every step and asked before changing files |

### Planning
I split the work into small steps and tested each part before moving on:
1. Setup (virtual environment, `.gitignore`, `.env`, GitHub)
2. Backend logic with the saved mock data (no API calls)
3. Tests with pytest
4. Connect the real API (heartBeat → arrivals/departures → query)
5. Menu and destination overview
6. Documentation and video

I started with mock data so I could build and test the logic without the network and without using up API requests.
I kept a running log of findings, decisions and problems in `docs/notes.md` while I worked.

### Problems and solutions during research
- **Problem:** I did not know the exact path for the health check.
  **Solution:** I found it in the Swedavia portal: `/heartBeat` (with a capital B).
- **Problem:** the documentation did not show exactly which fields a flight has.
  **Solution:** I called the API myself and saved a real response to study.
- **Problem:** the original code was only visible in a video, and some options were never shown running.
  **Solution:** I combined the video, the documentation and my own tests, and wrote down every assumption.

---

## Phase 2 – Implementation

### How the work started
I began with the setup: a virtual environment, `requirements.txt` with pinned versions, `pytest.ini`,
`.gitignore`, `.env` (with my key) and `.env.example` (a template without the key), and `config.py`, which reads the key.
Before the first commit I checked with `git status` that `.env` was **not** listed.

### How the project is structured
Instead of one large file, every module has one job:

| Module | Job |
|---|---|
| `config.py` | Settings: reads the key from `.env`, `BASE_URL`, `TIMEOUT`, the 10 airports |
| `formatting.py` | Turns raw flight data into readable text: time conversion, ghost filter, sorting, the flight layout |
| `api_client.py` | The **only** module that talks to the internet; turns every failure into a clear `ApiError` |
| `user_input.py` | Parses what the user types: airport, date, flight number |
| `destinations.py` | Counts flights per city and looks up the country in `city_country.json` |
| `airport.py` | The menu (entry point): paging, the seven options, and all error messages |

### Which parts were created first, and how they were developed
I built from the inside out: first the logic that works on data, then the network, then the user interface.

**1. `formatting.py` (with mock data)**
- `fmt_time` converts `"2026-09-28T20:25:00Z"` to `20:25 UTC → 22:25 CEST` with `datetime.fromisoformat` and
  `zoneinfo`. Bad or missing input returns `–` instead of crashing.
- `is_valid_flight` hides ghost entries but keeps cancelled flights.
- `is_upcoming` decides if a flight has not happened yet. It takes an optional `now` argument, so tests can use a
  fixed time (dependency injection).
- `format_flight` returns the text and `print_flight` only prints it, so the layout can be tested.
- Later: `sort_by_time`, because the API does not send the flights in time order.

**2. `api_client.py` (the real API)**
- `get()` is the only function that calls `requests.get`. Every request has a **10-second timeout**.
  Every failure becomes an `ApiError` with a clear message: 400, 401, 403, 404, 429, other codes, timeout,
  no network, and invalid JSON. The key is only sent in a header, never in a URL or an error message.
- `heartbeat()`, `get_arrivals()` and `get_departures()` build on `get()`.
- `query()` fetches page after page with the `continuationtoken`. Because the API sends a token even on the last page,
  it stops when the token is missing **or** when a page is not full, and never fetches more than 5 pages.
- `build_filter()` builds the OData filter, e.g. `airport eq 'ARN' and scheduled eq '260929' and flightType eq 'D'`.

**3. `user_input.py` ("validate at the edge")**
- `parse_airport` accepts `ARN`, `arn`, `Visby` or `Göteborg`.
- `parse_date` accepts `YYYY-MM-DD`, `today`, `tomorrow`, `yesterday`, `now` (and the Swedish words from the original).
- `parse_flight_id` only accepts A–Z and 0–9. This is a **security check**: input like `SK1' or airport eq 'GOT`
  can never change the OData filter.

**4. `airport.py` (the menu)**
- `show_flights` prints 50 flights per page, like the original.
- `ACTIONS` maps menu choices to functions instead of a long `if/elif` chain.
- **All errors are caught in one place** in `main`, so the user sees `⚠ <message>` and the menu comes back.
- The demo calls all four endpoints with a 2-second pause between them, and keeps going if one step fails.

**5. `destinations.py` + menu option 7**
- Counts flights per city, removes airport codes (`London LHR` → `London`) and looks up the country.
- `city_country.json` has the 138 cities that appear in my real data. If I was not sure about a city, I left it
  out, so it shows `[Unknown]` instead of a wrong country.

### Problems and solutions during implementation
- **Problem:** `.gitignore` had spaces at the start of every line, so `   .env` did not match `.env`.
  My API key would have been committed.
  **Solution:** I removed the spaces and checked with `git status` that `.env` was not listed.
- **Problem:** Windows Smart App Control blocked `pip.exe` ("an application control policy has blocked this file").
  **Solution:** I ran pip through Python: `python -m pip install ...` (and `python -m pytest` for the tests).
- **Problem:** I believed the API date was UTC and planned around a "UTC limitation".
  **Solution:** in the demo, the first arrival for 29 September was at 22:20 UTC on the 28th. I checked the mock data:
  the arrivals for one date cover exactly 00:00–23:59 **Swedish** time. So the date is the Swedish date, the limitation
  did not exist, and my code was already right.
- **Problem:** the original code read `continuationToken`, but the real key is `continuationtoken`, and a token comes
  back even on the last page.
  **Solution:** I tested with a query for a single flight to see the real behaviour, then built two stop conditions.

---

## Phase 3 – Completion

### Testing the whole solution
**Automatic tests:** 176 pytest tests, which run in under a second and **never call the real API**.
- Fakes replace `requests.get`, `input()`, the clock and the pauses, so every case can be tested on demand.
- Saved real responses are used as reality checks (e.g. 327 valid arrivals, 146 upcoming at noon).
- The security tests check that a missing key stops the app **before** any request, and that the key never appears in
  an error message.
- I also broke the code on purpose (`!=` → `==`) to see that the tests turn red.

**Manual tests against the real API**, one case at a time:

| Case | How I tested it | Result |
|---|---|---|
| Wrong API key | A fake key in the terminal (`$env:SWEDAVIA_API_KEY = "wrong-key-123"`) | `401` → clear message, no crash |
| Unknown airport | `XXX` | `400` → clear message |
| No network | Wi-Fi turned off | Clear "check your internet connection" message |
| Paging | `query(..., count=200)` for 342 departures | Page 1: 200, page 2: 142 → 342, same as the other endpoint |
| All menu options | `python airport.py`, options 1–7 | All work; the demo's departures and query steps gave the same number (299) |

### Improvements and optimization
| | Original | My version |
|---|---|---|
| API key | Hardcoded in the source code | Read from `.env`, never committed to GitHub |
| Errors (network, key, input) | Can crash | Clear message, the app never crashes |
| Tests | None visible | 176 pytest tests, no real API calls |
| Structure | Mostly one large file | Small modules with one job each |
| Paging in OData query | Read `continuationToken` (wrong case), so page 2 was probably never fetched | Reads `continuationtoken`, stops correctly, max 5 pages |
| Flight list order | Order from the API | Sorted by scheduled time |
| Destination overview | Separate script that runs once and exits | Menu option 7, everything in one place |

Small optimizations: airport and flight number are checked **before** calling the API (faster answer, fewer requests),
`query()` never uses more than 5 requests, and the demo pauses between requests to avoid the rate limit.

### Publishing and presentation
- The code is on GitHub with a README that explains setup, how to run the app and the tests.
- The key is only in `.env`, which is in `.gitignore`; `.env.example` shows what is needed.
- I recorded a video that walks through the phases and shows the app and the tests running.

### Problems and solutions during completion
- **Problem:** the first real `query()` test stopped with `429 Too Many Requests`.
  **Solution:** I waited a minute and it worked. The app's message ("Wait a moment and try again") was the right advice.
  I also added a 2-second pause between requests in the demo and in option 7.
- **Problem:** a wrong OData filter gave the message "Check the airport code and date", which was misleading.
  **Solution:** I changed the 400 message to "Check the airport code, date or filter."
- **Problem:** a green test expected Oslo 20 and London 13, but the app showed 15 and 12. The test counted ghost entries,
  which the app hides.
  **Solution:** the test now removes ghost entries first, like the app, so the test and the screen match.

---

## Phase 4 – Problems & Solutions (summary)

**Problem:** `.gitignore` had leading spaces, so my API key (`.env`) would have been committed.
**Solution:** removed the spaces and checked `git status` before the first commit.

**Problem:** Windows Smart App Control blocked `pip.exe` and `pytest.exe`.
**Solution:** used `python -m pip` and `python -m pytest`.

**Problem:** the API returns "ghost entries" (status `DEL`) with almost no data.
**Solution:** `is_valid_flight` hides them but keeps cancelled flights.

**Problem:** without error handling, API errors (wrong key, no network, timeout) end in a long, cryptic traceback
from `requests` (I saw it when I turned off Wi-Fi before the menu existed).
**Solution:** `api_client.get()` turns every failure into an `ApiError` with a clear message, and the menu catches it.

**Problem:** I did not know how `/query` answered (form of the data, where the token is, the date format).
**Solution:** small exploration calls with `count=5`. They showed wrapped flights, a lower-case `continuationtoken`,
and the date format `YYMMDD`.

**Problem:** the API sends a continuation token even on the last page, so "stop when there is no token" never stops.
**Solution:** also stop when a page has fewer flights than requested, and never fetch more than 5 pages.

**Problem:** `429 Too Many Requests` when making several requests quickly.
**Solution:** wait and try again; a 2-second pause between requests in the demo and option 7.

**Problem:** I assumed the API date was UTC.
**Solution:** checked the real data: the date is the Swedish date. Lesson: check assumptions against real data.

**Problem:** user input could have broken the OData filter (`SK1' or airport eq 'GOT`).
**Solution:** `parse_flight_id` only accepts letters A–Z and digits, and a test sends this input through the whole menu.

**Problem:** a green test did not test what the app shows (it counted ghost entries).
**Solution:** changed the test to follow the same path as the app.

---

## Conclusion

### What I achieved
I rebuilt the Swedavia FlightInfo app from a video: all seven menu options, 50 flights per page, Swedish time,
flight search, OData queries and the destination overview. My version keeps the API key out of the code, never crashes
on errors, has 176 automatic tests, and is split into small modules. It also fixes the paging in the OData query and
sorts the flights by time.

### What went well
- **Starting with mock data** let me build and test the logic without the network or the API quota.
- **Small steps with a commit after each one** made it easy to see what changed and to go back if needed.
- **Testing against real data** found things the documentation did not say: ghost entries, the lower-case token,
  the token on the last page, and that the date is the Swedish date.
- **One place for network code and one place for error messages** made the stability improvement simple.

### What went badly
- I almost committed my API key because of spaces in `.gitignore`. I only caught it because I checked `git status`.
- I trusted my reading of the documentation about UTC and planned around a problem that did not exist.
- One test was green but tested the wrong thing. A passing test is only useful if it follows the same path as the program.
- I hit the rate limit (429) because I made several requests too quickly while testing.

### What I learned
- How to reverse engineer an app: look at the output, ask questions, guess the inputs and the process, test the guesses.
- How to call a REST API safely: headers, timeouts, status codes, error handling, and keeping secrets in `.env`.
- How to write tests that do not depend on the network, with fakes, fixtures and `parametrize`.
- To write down assumptions and check them against real data.

### What could be improved
- For departures, show check-in desks and gate open/close times instead of the empty baggage line.
- Show "data updated X minutes ago" using the `last-modified-inminutes` response header.
- Show the full airport name (`Visby (VBY)`) instead of only the code.
- Handle 429 automatically, for example by reading the `Retry-After` header and trying again once.
- Treat different spellings of the same city (e.g. "Bucarest" and "Bucharest") as one.
