# Project notes – Swedavia FlightInfo

Running log of findings, problems, and solutions.
This is the raw material for DOCUMENTATION.md and the video.

---

## Phase 1 – Research
The goal of this phase was to understand how the original app works without having its source code.
I studied the video of the finished app, read Swedavia's API documentation, and tested the API myself.
Then I worked backwards from the output to the data, to guess the inputs and the logic behind it.

### What I found out about the original app
- It is a **Python terminal app**, not a web app.
- It uses the **Swedavia FlightInfo API v2** for Sweden's 10 Swedavia airports.
- Files: `airport.py` (menu), `destinationer.py` (destination overview),
  `city_country.json` (263 cities → 59 countries), README.md, FÖRKLARING.md.
- Menu: 1 Arrivals, 2 Departures, 3 Search flight, 4 OData query, 5 HeartBeat, 6 Demo, q Quit.
- Shows 50 flights per page: [Enter] next page, [a] show all, [q] back.
- Converts UTC to Swedish time (CET/CEST).
- The destination overview was a separate script (`destinationer.py`) that ran once and exited.
- **The video never showed options 3 and 6 running, so I based them on the menu text and documented my
  assumptions** (see "Step 5 – menu: what the video showed, and my assumptions" below).

### Weaknesses I noticed in the original
- The **API key was hardcoded** in the source code (visible in the video).
- No visible tests.
- Most of the code is in one large file.

### API testing in the Swedavia portal (2026-09-28)
- Got a free API key (10,000 requests/month).
- `GET /heartBeat` → `200 OK`, body `"IsAlive"` (a JSON string, not an object).
- `GET /ARN/arrivals/2026-09-28` → `200 OK`, 365 flights.
- Findings from the JSON:
  - Fields can be missing: only `scheduledUtc` existed (no estimated/actual), `baggage` was empty, no `gate`.
  - `flightLegStatus: "DEL"` = deleted from the schedule. Cancelled flights have a separate status, `CAN`.
  - `diIndicator`: I = International, D = Domestic, and also `S` (probably Schengen, not verified).
  - 365 flights in one day explains why the original uses paging.
- Saved sample responses in `mock_data/` to use in tests.

### Findings from the mock data (ARN, 2026-09-28)
- 365 flights: 38 `DEL`, 3 `CAN`, the rest `SCH` (scheduled) or `LAN` (landed).
- The 38 `DEL` entries are **ghost entries**: they come first in the list and have almost no data
  (only a scheduled time, empty baggage, no gate).
- All times use the same format, e.g. `"2026-09-28T20:25:00Z"` (UTC). Seconds are not always zero.
- Missing times are left out completely (never `null` or `""`).
- Verified field names: gate = `locationAndStatus.gate` (often missing),
  baggage belt = `baggage.baggageClaimUnit`, status text = `flightLegStatusEnglish` (e.g. "Landed 23:39").
- Check: flight JTD664 has actual time 21:39 UTC, and my code converts it to 23:39 CEST,
  the same as Swedavia's own status text "Landed 23:39".

### Tools chosen
- Python 3.14, `requests`, `python-dotenv`, `pytest`, `tzdata` (time zone data, which Windows does not have built in)
- Versions are pinned with `==` in `requirements.txt`, so everyone gets the same setup.
- VS Code + Claude as a coding assistant (asks before every change)
- Git + GitHub

### Planning
Build step by step and test each part before moving on:
1. Setup (virtual environment, `.gitignore`, `.env`, GitHub)
2. Backend logic using saved sample data (no API calls)
3. Tests with pytest
4. Connect the real API (heartBeat → arrivals/departures → query)
5. Menu and destination overview
6. Documentation and video

I started with sample data so I could test my logic without depending on the network
or using up API requests.

### Problems and solutions during research
- **Problem:** I did not know the exact path for the health check.
  **Solution:** found it in the Swedavia portal: `/heartBeat` (capital B).
- **Problem:** the documentation did not show exactly which fields a flight has.
  **Solution:** tested the API myself and saved a real response to study.
- **Problem:** the original app's code was only visible in a video.
  **Solution:** combined what I saw in the video with the documentation and my own tests.
  
---

## Phase 2 – Implementation

### Problem: `python3` / `python` not found on Windows
- **Cause:** Windows has an alias that points to the Microsoft Store instead of Python.
- **Solution:** used the `py` launcher (`py --version` → Python 3.14.7).

### Problem: project folder was inside OneDrive
- **Risk:** OneDrive tries to sync thousands of small files in `.venv`, which can be slow and break the environment.
- **Solution:** moved the project to `C:\Users\gabri\Projekt\flightinfo`. The code is backed up on GitHub instead.

### Problem: PowerShell blocked the venv activation script
- **Error:** "running scripts is disabled on this system".
- **Cause:** PowerShell's default ExecutionPolicy blocks all scripts.
- **Solution:** `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`
  (allows my own local scripts, only for my user account).

### Problem: `.gitignore` did not ignore `.env`
- **Cause:** every line in `.gitignore` started with spaces. Git treats leading spaces as part of
  the file name, so `   .env` did not match `.env`. My API key would have been committed.
- **Solution:** removed the spaces. Checked with `git status` after `git init` that `.env` is not listed.

### Problem: Windows blocked `pip.exe`
- **Error:** "En programkontrollprincip har blockerat den här filen" (an application control policy blocked the file).
- **Cause:** Windows Smart App Control blocks `.venv\Scripts\pip.exe` because it is created locally and is not signed.
- **Solution:** run pip through Python instead: `python -m pip install -r requirements.txt`.
  The same applies to pytest: `python -m pytest`.

### Design decisions in `formatting.py`
- **`fmt_time`:** uses `datetime.fromisoformat` and `zoneinfo` (`Europe/Stockholm`), so summer time (CEST)
  and winter time (CET) are handled automatically. Bad or missing input returns `–` instead of crashing.
- **`is_valid_flight`:** skips ghost entries (no flight id, no scheduled time, or status `DEL`).
  Cancelled flights (`CAN`) are kept, because travellers need to see them. 327 of 365 flights are valid.
- **`is_upcoming`:** uses actual → estimated → scheduled time. It takes an optional `now` argument,
  so tests can use a fixed time (dependency injection). Default `now=None`, not `now=datetime.now()`,
  because Python evaluates default values only once.
- **`get_time_info`:** small helper, so "arrivalTime or departureTime" is written in one place only.
- **`format_flight` / `print_flight`:** `format_flight` returns the text and `print_flight` only prints it
  (separation of concerns), so the formatting can be tested.
- **Differences from the original output:** `–` for every missing value (the original mixed `N/A` and `–`),
  and `To` shows the IATA code when the airport name is missing (the original showed `(ARN)`).

### Tests for `formatting.py` (step 3)
- `tests/test_formatting.py`: **36 tests, all passing in 0.22 s** (`python -m pytest -v`).
- No real API calls. Two kinds of test data:
  - small handmade flights (`make_flight(...)`), one test per rule, so it is clear what is tested;
  - the saved mock data as a reality check: 365 flights → 327 valid, 146 upcoming at 12:00 UTC,
    and flight JTD664 printed with all fields.
- `is_upcoming` is tested with a fixed time (`NOON_UTC`), so the result is the same whenever the tests run.
- Edge cases covered: summer/winter time, the clock change day (25 Oct 2026: 00:30 UTC → 02:30 CEST,
  01:30 UTC → 02:30 CET), time past midnight, missing or broken values, input that is not a dict.
- pytest features used: `assert`, `@pytest.mark.parametrize` (same test, many inputs),
  `@pytest.fixture` (loads the mock file), `capsys` (captures `print()` output).
- `pytest.ini` sets `pythonpath = .` so the tests can import modules from the project root,
  and `testpaths = tests` so pytest only looks in `tests/`.

### Design decisions in `api_client.py` (step 4, part 1)
- **One function talks to the internet:** `get(path, params)`. All other functions (`heartbeat`,
  later `get_arrivals` etc.) call it, so error handling is written in one place only.
- **Every request has `timeout=TIMEOUT` (10 s).** Without a timeout, `requests` can wait forever
  and the app looks frozen.
- **Every failure becomes an `ApiError` with a clear message** (instead of printing and returning `None`).
  The menu will catch it and show the message. Same idea as `MissingApiKeyError` in `config.py`.
  - HTTP 400/401/403/404/429 each have their own message; other codes get a general message.
  - `requests.Timeout` → "did not answer within 10 seconds", `requests.ConnectionError` → "check your
    internet connection", any other `requests` error → its type name.
  - A response that is not valid JSON → `ApiError`.
- **The key is only sent in a header**, never in the URL or in an error message.
- `heartbeat()` returns `True` if the API answers `"IsAlive"`. Errors are passed on as `ApiError`,
  so the user sees *why* it failed.
- First real call: `heartbeat()` → `True` (2026-09-29).

### Tests for `api_client.py`
- `tests/test_api_client.py`: 20 tests. Total so far: **56 passed in 0.36 s**.
- **No real API calls:** `monkeypatch` replaces `requests.get` with a fake function that returns a
  small `FakeResponse` (status code + JSON) or raises an error (e.g. `requests.Timeout()`).
  This saves API quota, works without network, and lets me create errors on demand.
- A fixture with `autouse=True` sets a fake key (`"test-key"`) in every test, so the real key is never used.
- Covered: correct URL, headers and timeout; each HTTP error; timeout; no network; invalid JSON;
  missing key stops *before* any request; the key never appears in an error message; heartbeat.
- I chose `monkeypatch` + my own `FakeResponse` over `unittest.mock.MagicMock` because it is explicit:
  I can see exactly what the fake does.

### Error handling checked against the real API (2026-09-29)
| Case | How I tested it | Result |
|---|---|---|
| Wrong API key | `$env:SWEDAVIA_API_KEY = "wrong-key-123"` in the terminal, then `heartbeat()` | **401** → `ApiError: The API key was rejected (401). Check SWEDAVIA_API_KEY in .env.` |
| Unknown airport | `get('/XXX/arrivals/2026-09-29')` | **400** (not 404) → `ApiError: The API did not accept the request (400). Check the airport code and date.` |
| No network | Wi-Fi turned off, then `heartbeat()` | `socket.gaierror` → `urllib3` `NameResolutionError` → `requests.ConnectionError` → `ApiError: Could not connect to the API. Check your internet connection.` |

- Trick: `load_dotenv()` does not overwrite an environment variable that already exists, so a fake key
  set in the terminal wins over `.env`. I never had to edit `.env`. Afterwards: `Remove-Item Env:SWEDAVIA_API_KEY`.
- The traceback is shown only because no menu catches the error yet (step 5 will).
- I did not know in advance if an unknown airport gives 400 or 404, so both have a message.
  The real API answered 400. Idea for step 5: check the code against `AIRPORTS` in `config.py`
  *before* calling the API. That gives a faster, clearer message and saves requests.
- Without network the lookup of `api.swedavia.se` fails at once, so it becomes a connection error,
  not a timeout. The traceback is long because Python shows the whole chain of errors
  ("During handling of the above exception, another exception occurred"). Read it from the bottom up.
  Without my error handling, the user would only see this cryptic chain.
- Timeout could not easily be forced against the real API, so it is covered by the mocked test only.

### `get_arrivals` / `get_departures` (step 4, part 2)
- Both call one shared helper, `_get_flights(direction, iata, day)`, because the URLs only differ in one word.
- They take a `datetime.date`, not text. The menu will turn user input ("today", "2026-09-29") into a date
  ("validate at the edge"), so the API client always gets a correct date. The API date is in **UTC**.
- They return only the list of flights. Missing `flights` → `[]`. A response that is not a dict → `ApiError`
  (an empty list would hide a real problem).
- 6 new tests with the fake `requests.get`. Total: **62 passed in 0.44 s**.

### Findings: real departures (ARN, 2026-09-29, saved as `mock_data/departures_sample.json`)
- My guess was right: the top level has `from` (not `to`), each flight has `departureTime` and `arrivalAirportEnglish`.
- 342 flights: 146 `ACT` ("Departed", all with `actualUtc`), 98 `SCH`, 53 `SEQ` ("Estimated 16:45" etc.),
  43 `DEL` (ghost entries), 2 `CAN`. → 299 valid departures.
- Departures have **no `baggage`**. Instead they have `checkIn` (`checkInDeskFrom`/`checkInDeskTo`) and gate info
  (`gate`, `gateOpenUtc`, `gateCloseUtc`, `gateActionEnglish` e.g. "Gate closed").
- Strange: 53 flights say "Estimated ..." in the status text, but only 4 have an `estimatedUtc` field. Not explained yet.
- `formatting.py` works for departures without changes: `get_time_info` finds `departureTime`,
  `From` falls back to `ARN` from `flightLegIdentifier`, and `Baggage` shows `–`.
- 4 new tests with the real departures data prove this (299 valid, the 146 departed flights are not
  upcoming, `From : ARN`, `To` = destination, `Baggage : –`). Total: **66 passed in 0.27 s**.

### Research: the `/query` endpoint (step 4, part 3)
From Swedavia's PDF "Using the FlightInfo API":
- OData filter with the fields `airport`, `flightType` ('A' = arrivals, 'D' = departures), `scheduled`, `flightId`,
  and the operators `eq`, `and`, `or` (parentheses allowed). Without a filter: all flights.
- Example: `airport eq 'ARN' and scheduled eq '180209' and flightType eq 'D' and flightId eq 'SK007'`
- `count`: default and max 1000. `continuationtoken`: "used for getting next page or flights changed since last request".

Checked with a small exploration script (outside the project, `count=5`, the key is never printed), 2026-09-29:
- The date format `scheduled eq '260929'` (**YYMMDD**) works, as in the documentation.
- The response is a dict: `flights` (list) + `continuationtoken`.
- **Surprise 1:** each flight is **wrapped**: `{"departure": {...}}` or `{"arrival": {...}}`. Inside is exactly the
  same flight as from `/ARN/arrivals/...`, so `formatting.py` works after unwrapping.
- **Surprise 2:** the key is **`continuationtoken`** (lower-case t). The original code read `data.get("continuationToken")`,
  which would always give `None`, so its paging probably never fetched page 2
  (unless the API has changed since the video was recorded).
- The token looks like base64 (e.g. `H4sIAAAA...AAAA=`), so it can contain `+ / =`. `requests` URL-encodes
  values in `params` automatically, so I do not need to do it myself.
- **Surprise 3:** the API sends a `continuationtoken` **even on the last page**. Test: a query for one single
  flight (`flightId eq 'D83209'`) returned 1 flight *and* a token. So "stop when there is no token" alone
  would never stop, and the loop would always use `max_pages` requests.
  **Solution:** stop when the token is missing **or** when a page has fewer flights than `count`.

### `query()` and `unwrap_flight()`
- `query(filter_text, count=1000, max_pages=5)` loops with `for _ in range(max_pages)` (cannot loop forever),
  unwraps every item and adds the token to `params` for the next page. Returns a plain list of flights,
  the same shape as `get_arrivals()`, so the menu can use `is_valid_flight` / `print_flight` everywhere.
- 12 new tests with a fake `requests.get` that returns one page per call (`iter()` + `next()`).
  It saves a **copy** of `params` for every call, because `query()` changes the same dict between calls.
  Total: **78 passed in 0.40 s**.

### Problem: 429 Too Many Requests during the real `query()` test
- **What happened:** `query(..., count=200)` for ARN departures (342 flights, so 2 pages) stopped with
  `ApiError: Too many requests (429). Wait a moment and try again.` My error handling worked: clear message, no crash.
- **Cause:** a rate limit (requests per time unit), not the monthly quota. Only about 10 requests had been used that day.
  The exact limit is not known.
- **Solution:** waited 1 minute and ran the same query again. It worked: **342 flights** (page 1: 200, page 2: 142),
  the same number as `/ARN/departures/2026-09-29`, and the first flight (BA779B) is the same too.
  So the 429 was temporary (several requests close together earlier), and no code change was needed.
  The message "Wait a moment and try again" was the right advice.
- This also proves that paging works against the real API (page 2 was fetched, then the loop stopped).

### Step 5 – menu: what the video showed, and my assumptions
What I saw in the original (menu text translated from Swedish):
- Airport question: "Enter IATA code or city name (e.g. ARN or Visby)", with the list of the 10 airports shown first.
  An unknown airport gave "⚠ Unknown airport, try again" and asked again (a `while True` loop).
- Date question: "Enter date (YYYY-MM-DD / now / today / tomorrow / yesterday)".
- ARN showed "Showing 50/220" and later "50/217" while the API had ~365 flights, and the code had both
  `_is_valid_flight` and `_is_upcoming`. The number went down during the recording.
- Menu 3 was "Search for a specific flight number", menu 6 was "Demonstrate all endpoints automatically".
  The video never shows these two being run.
- The destination overview was a **separate script** (`destinationer.py`) that ran once and exited:
  choose airport → date → optional filter (country or city) → prints cities with country and number of flights,
  e.g. "Frankfurt (5st) [Germany]".

My decisions (**assumptions** where the video does not show it):
- **Showing flights:** always hide ghost entries (`is_valid_flight`). When the user types `now`, also hide flights
  that have already landed/departed (`is_upcoming`). _Assumption_, based on 220 < 365 and the number going down.
- **Menu 3, search flight:** ask for flight number + airport + date and build the `/query` filter with `build_filter()`.
  _Assumption_: the video does not show which inputs were needed.
- **Menu 6, demo:** call all four endpoints in a row (heartBeat, arrivals, departures, query) with fixed example
  values and show a short result from each. _Assumption_: the video does not show it running.
- **Destination overview:** menu option **7** instead of a separate script. Improvement: everything in one place.
- **Language:** English menu texts, the same as the code, error messages and docs (the original was in Swedish).
- **UTC limitation (accepted):** the API date is a UTC date. Flights between 00:00 and 02:00 Swedish time
  (summer) belong to the next UTC date. I document this instead of making two requests per search.
- **Structure:** input parsing goes in its own module, `user_input.py` (testable, "validate at the edge").
  The airport is checked against `AIRPORTS` before any API call. Flight numbers may only contain letters and digits,
  so user input cannot break the OData filter (e.g. `SK1' or airport eq 'GOT`).

### `user_input.py` (step 5a)
- **`parse_airport(text)`**: accepts an IATA code (`arn`) or a whole word of the airport name (`Visby`, `arlanda`,
  `GÖTEBORG`), or the full name. Only whole words count, so `"a"` does not match everything.
  `"Stockholm"` matches both ARN and BMA; the first in `AIRPORTS` (ARN) wins, and a test documents this choice.
  Returns `None` for unknown input, so the menu can ask again (like the original's `while True`).
- **`parse_date(text, today=None)`**: accepts `now`, `today`, `tomorrow`, `yesterday` (and the Swedish words
  `nu`, `idag`, `imorgon`, `igår` from the original) or `YYYY-MM-DD`. Returns a tuple `(date, upcoming_only)`:
  `now` → `(today, True)`, everything else → `(date, False)`. Invalid input (`2026-02-30`, `29/9`) → `None`.
  "Today" is the **Swedish** date, because that is what the user means. `today` can be passed in tests
  (same idea as `now` in `is_upcoming`). `timedelta` handles month ends (30 Sep + 1 day = 1 Oct).
- 31 tests in `tests/test_user_input.py`. Total: **109 passed in 0.33 s**.
- **`parse_flight_id(text)`**: removes spaces and dashes and makes it upper case (`"sk 532"` → `"SK532"`).
  Only 2–8 characters A–Z/0–9 are accepted (`isascii()` + `isalnum()`). This is the **security check**:
  a `'` can never reach the OData filter, so `SK1' or airport eq 'GOT` is rejected (a small injection test).
  `isascii()` is needed because `isalnum()` also accepts letters like `Å`.
- **`build_filter(airport, day, flight_type=None, flight_id=None)`** is in `api_client.py`, not `user_input.py`,
  because it is about the API's filter language (field names, `eq`, YYMMDD). `{day:%y%m%d}` gives `260929`.
  Without `flight_type` the search finds both arrivals and departures. The values must already be validated.
  _Not verified yet:_ whether the API finds `SK532` if the flight is stored as e.g. `SK0532`.
- 15 more tests. Total: **124 passed in 0.35 s**.

### `show_flights()` in `airport.py` (step 5b)
- Prints 50 flights per page, like the original: `── Showing 50/327 ── (277 left)` and
  `[Enter] next page | [a] show all | [q] back to menu`. Numbering continues on the next page (`[51]`),
  because `enumerate(..., start=shown + 1)`. The last page does not ask. An unknown answer works like Enter.
- `ask=input` is an optional argument, so tests pass a fake `input()` that returns fixed answers
  and records every prompt (same idea as `now` and `today`). Functions can be passed as arguments in Python.
- 7 tests in `tests/test_airport.py`, using `page_size=2` so 5 small flights are enough.
- Tried it by hand with the mock data (327 valid arrivals): it looks like the original.
- **Observation:** the flights come in the order the API sends them, **not sorted by time**
  (e.g. [1] at 19:45, [73] at 00:05, [90] at 06:55). I do not know if the original sorted them.
- **Decision / improvement:** sort by **scheduled** time with `sort_by_time()` in `formatting.py`, like a departure
  board (the estimated time changes, so flights would jump around). `sorted(..., key=...)` returns a new list.
  The time strings all have the same format (year first), so they sort correctly as text.
  The key `(text == "", text)` puts flights without a time last (`False` sorts before `True`).
  4 tests, including all 327 real arrivals in time order. Total: **135 passed in 0.39 s**.
- Original app: _(fill in: what happened in the video / what would happen with a wrong key?)_

---

## Phase 3 – Completion
_(fill in later)_

---

## Improvements compared to the original
| | Original | My version |
|---|---|---|
| API key | Hardcoded in code | `.env`, never on GitHub |
| Errors (network, key, input) | Can crash | Clear message, never crashes |
| Tests | None visible | pytest (135 tests so far), no real API calls |
| Flight list order | Order from the API (not sorted, as far as I can tell) | Sorted by scheduled time |
| Paging in OData query | Read `continuationToken` (wrong case), so page 2 was probably never fetched | Reads `continuationtoken`, stops on missing token **or** a non-full page, max 5 pages |
| Structure | Mostly one large file | Small modules, one job each |
| Destination overview | Separate script (`destinationer.py`), runs once and exits | Menu option 7, everything in one place |

---

## Ideas (maybe later)
- ~~Option to hide deleted flights (`DEL`).~~ Done: `is_valid_flight` hides them by default.
- Show "data updated X min ago" using the `last-modified-inminutes` header.
- For departures, show check-in desks (`checkIn`) and gate open/close times instead of the empty `Baggage` line.