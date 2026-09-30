# CLAUDE.md – Swedavia FlightInfo (Reverse Engineer a Result)

## About this project
APL assignment "Reverse Engineer a Result". I have watched a finished app (a Python
terminal client for the Swedavia FlightInfo API v2) and I am rebuilding **the same app,
but improved**. It must have the same features as the original (menu 1–6 + q, arrivals,
departures, flight search, OData query, HeartBeat, demo, 50-per-page paging, destination overview).
The goal is that I **understand** every part, not just that it works.

## Improvements over the original (in scope)
1. **Security:** the original had the API key hardcoded. Mine reads it from `.env` (in `.gitignore`).
2. **Stability:** error handling for wrong key (401), bad airport/date, timeouts, no network, and missing fields in the JSON. The app shows a clear message and never crashes. All requests use a timeout.
3. **Tests:** pytest tests for the logic and the API client (with mocked requests).
4. **Clean structure:** code split into small modules instead of one big file.

Out of scope unless I ask: colored terminal output (rich), web UI, caching, export.

Deadline: Thursday. Documentation, README, and code comments are written in *English**.

## About me
- Career changer with over 20 years of professional experience in personal assistance,
  most recently as account manager, responsible for 50–70 assistants, client relationships,
  and system ownership of the scheduling and administration tools.
- Completing a web development program (Komvux, graduating October 2026) with workplace
  training (APL) in AWS, DevOps, Terraform, CI/CD, and QA.
- I bring strong skills in responsibility, structured problem-solving, and communication
  into software development.
- I am building my Python skills through this project. I want explanations that build real
  understanding (what → why → how), so that I can make and defend my own technical decisions.
- Talk to me in **Swedish**. Code, comments, commit messages, and docs are in English.

## Working rules (important)
1. **Always ask before you create, change, or delete files, or run commands.**
   Show a short plan first and wait for my "ok".
2. Work in **small steps**: one function or one file at a time.
3. After each step: explain what the code does, run the tests, and suggest a commit message. I do the commit myself.
4. If there are several ways to do something: compare them briefly, recommend one, and explain why.
5. If you are unsure (e.g. how the API responds), say so. Do not guess.
6. Never put the API key in code, in logs, or in commits. It is only read from `.env`.
7. **Always give me step-by-step instructions for what I should do myself**: numbered steps with the exact command to run, which file to open, and where to click in VS Code/GitHub.
Say what I should see if it worked. Give me one step at a time and wait for me to say
"done" (or show the error) before the next one.
8. Keep `docs/notes.md` up to date yourself: write problems + solutions, findings and design decisions into it directly after each step (no need to ask first), and tell me what you added.

## My environment
- **Windows + PowerShell** in VS Code. Give PowerShell commands, not Mac/Linux commands.
- Project folder: `C:\Users\gabri\Projekt\flightinfo` (moved out of OneDrive on purpose).
- Python 3.14 via the `py` launcher. `python3`/`python` do not work outside the venv.
- `.venv` is **already created and activated** (`.\.venv\Scripts\Activate.ps1`).
  ExecutionPolicy is set to RemoteSigned for my user.
- Inside the activated venv, use `python`.
- Windows Smart App Control blocks `pip.exe` and `pytest.exe` in the venv.
  Always use `python -m pip ...` and `python -m pytest ...`.

## Current status
- Done: API key obtained, heartBeat and arrivals tested in the Swedavia portal,
  `mock_data/` samples saved, `.venv` created, packages installed.
- Step 1 done: `.gitignore` (fixed leading spaces), `requirements.txt` (pinned),
  `pytest.ini`, `.env.example`, `config.py` (key verified to load).
  Git repo on `main`, pushed to https://github.com/GabyCM78/flightinfo (`.env` not tracked).
- Step 2 done: `formatting.py` with fmt_time, get_time_info, is_valid_flight,
  is_upcoming (takes optional `now` for tests), format_flight, print_flight.
- Step 3 done: `tests/test_formatting.py`, 36 tests, all passing (`python -m pytest -v`).
- Step 4 part 1 done: `api_client.py` with `ApiError`, `get()` (timeout, clear error messages)
  and `heartbeat()` (real call returned True). `tests/test_api_client.py` uses monkeypatch +
  `FakeResponse`, fake key "test-key". 56 tests passing.
- Real error cases checked: wrong key → 401, airport XXX → 400, no network → ConnectionError.
- Step 4 part 2 done: `get_arrivals`/`get_departures` (take a `datetime.date`, return the flights list).
  Real departures saved as `mock_data/departures_sample.json`, and `test_formatting.py` has
  4 tests using it. 66 tests passing.
- Step 4 part 3 done: `query()` + `unwrap_flight()`, `MAX_PAGES = 5`. Real test: 342 flights over 2 pages.
  78 tests passing. **Step 4 done.**
- Step 5 plan: 5a `user_input.py` → 5b `show_flights` (paging) → 5c menu in `airport.py`
  → 5d `destinations.py` as **menu option 7**. Menu decisions/assumptions are in docs/notes.md
  ("Step 5 – menu"). English menu texts; Swedish date words also accepted.
- 5a done: `user_input.py` with `parse_airport`, `parse_date` (returns `(date, upcoming_only)`, "now" → True),
  `parse_flight_id` (A–Z/0–9 only); `build_filter` in `api_client.py`. 124 tests passing.
- 5b done: `show_flights()` (50 per page) + `sort_by_time()` in formatting.py.
- 5c done: menu in `airport.py` with options 1–6 + q (`ACTIONS` dict, all errors caught in `main`,
  demo with `DEMO_PAUSE = 2` s between requests). All options tried against the real API.
- 5d done: `destinations.py` + `city_country.json` (138 cities from the real mock data) as menu option 7
  (1 = departures, 2 = arrivals, 3 = both). `REQUEST_PAUSE = 2` s. 176 tests passing. **Step 5 done.**
- Next: step 6, README.md and docs/DOCUMENTATION.md (Phase 1–4 + Conclusion) from docs/notes.md, then the video.

## Tech stack
- Python 3.14 in a virtual environment (`.venv`)
- `requests` (HTTP), `python-dotenv` (reads `.env`), `pytest` (tests)
- Standard library: `datetime`, `zoneinfo` (Swedish time), `json`
- Note: on Windows, `zoneinfo` needs the `tzdata` package (included in `requirements.txt`).

## API facts (Swedavia FlightInfo v2) – verified
- Base URL: `https://api.swedavia.se/flightinfo/v2`
- Headers: `Ocp-Apim-Subscription-Key: <key>` and `Accept: application/json`
- `GET /heartBeat` → `200 OK`, body is the JSON **string** `"IsAlive"` (not an object).
  Optional query param `evaluationId` (we do not use it). Note the capital B.
- `GET /{IATA}/arrivals/{yyyy-mm-dd}` and `GET /{IATA}/departures/{yyyy-mm-dd}` (date = **Swedish local date**,
  verified: arrivals for 2026-09-28 go from 27T22:00Z to 28T21:55Z, i.e. 00:00–23:59 Swedish time)
- `GET /query?filter=...&count=...&continuationtoken=...` (max 1000 per page; `requests` URL-encodes the token).
  Filter fields: `airport`, `flightType` ('A'/'D'), `scheduled` (**YYMMDD**, e.g. '260929'), `flightId`;
  operators `eq`, `and`, `or`, parentheses. Response: `{"flights": [...], "continuationtoken": "..."}`.
  Each item is **wrapped**: `{"arrival": {...}}` or `{"departure": {...}}`. The token key is lower-case and
  is sent **even on the last page**.
- Rate limit exists (got a temporary 429 after several quick requests); exact limit unknown.
- Response headers include `last-modified` and `last-modified-inminutes`.
- Free tier: 10,000 requests/month, so tests use mock data and never call the real API.
- Airports: ARN, GOT, BMA, MMX, LLA, UME, OSD, VBY, RNB, KRN

## Arrivals response structure (real example, ARN 2026-09-28)
```json
{
  "to": {
    "arrivalAirportIata": "ARN",
    "arrivalAirportEnglish": "Stockholm ARN",
    "flightArrivalDate": "2026-09-28"
  },
  "numberOfFlights": 365,
  "flights": [
    {
      "flightId": "BA778B",
      "departureAirportEnglish": "London LHR",
      "airlineOperator": { "iata": "BA", "icao": "BAW", "name": "British Airways" },
      "arrivalTime": { "scheduledUtc": "2026-09-28T20:25:00Z" },
      "locationAndStatus": {
        "terminal": "T2",
        "flightLegStatus": "DEL",
        "flightLegStatusEnglish": "Deleted"
      },
      "baggage": {},
      "codeShareData": [],
      "flightLegIdentifier": { "callsign": "BAW778B", "departureAirportIata": "LHR", "arrivalAirportIata": "ARN" },
      "remarksEnglish": [],
      "viaDestinations": [],
      "diIndicator": "I"
    }
  ]
}
```
Observations:
- **Fields can be missing or empty**: here only `scheduledUtc` exists (no `estimatedUtc`/`actualUtc`),
  `baggage` is `{}`, and `gate` is missing. Always use `.get()` with a default.
- Departures (verified, `mock_data/departures_sample.json`, ARN 2026-09-29, 342 flights): top level `from`,
  flights have `departureTime` and `arrivalAirportEnglish` (no `departureAirportEnglish`), **no `baggage`**
  but `checkIn` (`checkInDeskFrom`/`To`) and gate info (`gateOpenUtc`, `gateCloseUtc`, `gateActionEnglish`).
  Extra statuses: `ACT` = Departed, `SEQ` = "Estimated HH:MM" (only 4 of 53 have `estimatedUtc`).
  43 DEL → 299 valid.
- `diIndicator`: I = International, D = Domestic, S = seen in data (probably Schengen, not verified).
- Verified field names: gate is `locationAndStatus.gate` (often missing),
  baggage belt is `baggage.baggageClaimUnit`, `flightLegStatusEnglish` is e.g. "Landed 23:39".
- Mock data ARN 2026-09-28: 365 flights, 38 ghost entries (DEL), 3 cancelled (CAN) → 327 valid.
- `flightLegStatus`: `DEL` = deleted from the schedule (ghost entry), `CAN` = cancelled,
  `SCH` = scheduled, `LAN` = landed.
- ~365 flights per day at ARN, which is why the original shows 50 per page.

## How the original app printed a flight (from the video; menu text translated from Swedish)
```
[50] → SK532 | SAS Scandinavian Airlines (SK)
  From : London LHR
  To   : (ARN)
  Status   : Scheduled
  Terminal : T5   Gate: N/A
  Baggage  : 3
  Sched : 16:25 UTC → 17:25 CET
  Est   : –
  Actual: –
  D/I   : I
── Showing 50/220 ── (170 left)
[Enter] next page | [a] show all | [q] back to menu
```

## Project structure (target)
```
flightinfo/
├── CLAUDE.md
├── PLAN.md
├── README.md
├── requirements.txt
├── pytest.ini              # pythonpath = . and testpaths = tests
├── .env                    # SWEDAVIA_API_KEY=...  (never committed)
├── .env.example            # SWEDAVIA_API_KEY=your-key-here
├── .gitignore              # .venv/ .env __pycache__/ .pytest_cache/
├── config.py               # reads the key from .env, BASE_URL, AIRPORTS
├── formatting.py           # fmt_time, get_time_info, is_valid_flight, is_upcoming, format_flight, print_flight
├── api_client.py           # ApiError, get(), heartbeat(), get_arrivals(), get_departures(), unwrap_flight(), query(), build_filter()
├── user_input.py           # parse_airport(), parse_date(), parse_flight_id()
├── destinations.py         # city → country, destination overview
├── city_country.json
├── airport.py              # main menu (entry point)
├── mock_data/
│   ├── heartbeat_sample.txt   # exists
│   ├── arrivals_sample.json   # exists
│   └── departures_sample.json # exists
├── tests/
│   ├── test_formatting.py  # exists, 36 tests
│   ├── test_api_client.py  # exists, mocks requests, no real calls
│   ├── test_user_input.py  # exists
│   ├── test_airport.py     # exists, fake input()
│   └── test_destinations.py # exists
└── docs/
    ├── notes.md            # running log of problems and solutions (exists)
    └── DOCUMENTATION.md    # Phase 1–4 + Conclusion, per the school's guide
```

## Build order
Backend logic with mock data → tests → real API → menu → destinations → docs.
See PLAN.md. Always ask which step we are on before starting.