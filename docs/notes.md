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
| Tests | None visible | pytest (66 tests so far), no real API calls |
| Structure | Mostly one large file | Small modules, one job each |

---

## Ideas (maybe later)
- ~~Option to hide deleted flights (`DEL`).~~ Done: `is_valid_flight` hides them by default.
- Show "data updated X min ago" using the `last-modified-inminutes` header.
- For departures, show check-in desks (`checkIn`) and gate open/close times instead of the empty `Baggage` line.