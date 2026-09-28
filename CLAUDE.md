# CLAUDE.md – Swedavia FlightInfo (Reverse Engineer a Result)

## About this project
APL assignment "Reverse Engineer a Result". I have watched a finished app (a Python
terminal client for the Swedavia FlightInfo API v2) and I am rebuilding **the same app,
but improved**. It must have the same features as the original (menu 1–6 + q, arrivals,
departures, flight search, OData query, HeartBeat, demo, 50-per-page paging, destination overview).
The goal is that I **understand** every part, not just that it works.

## Improvements over the original (in scope)
1. **Security:** the original had the API key hardcoded. Mine reads it from `.env` (in `.gitignore`).
2. **Stability:** error handling for wrong key (401), bad airport/date, timeouts, no network,
   and missing fields in the JSON. The app shows a clear message and never crashes.
   All requests use a timeout.
3. **Tests:** pytest tests for the logic and the API client (with mocked requests).
4. **Clean structure:** code split into small modules instead of one big file.

Out of scope unless I ask: colored terminal output (rich), web UI, caching, export.

Deadline: Thursday. Documentation, README, and code comments are written in **English**.

## About me
- I am a career changer, studying web development and doing APL in AWS/DevOps/QA.
- I am fairly new to Python. Explain simply: **what → why → how**, with concrete examples.
- Do not talk down to me. I want to be able to solve similar problems myself.
- Talk to me in **Swedish**. Code, comments, commit messages, and docs are in English.

## Working rules (important)
1. **Always ask before you create, change, or delete files, or run commands.**
   Show a short plan first and wait for my "ok".
2. Work in **small steps**: one function or one file at a time.
3. After each step: explain what the code does, run the tests, and suggest a commit message.
   I do the commit myself.
4. If there are several ways to do something: compare them briefly, recommend one, and explain why.
5. If you are unsure (e.g. how the API responds), say so. Do not guess.
6. Never put the API key in code, in logs, or in commits. It is only read from `.env`.
7. **Always give me step-by-step instructions for what I should do myself**: numbered steps
   with the exact command to run, which file to open, and where to click in VS Code/GitHub.
   Say what I should see if it worked. Give me one step at a time and wait for me to say
   "done" (or show the error) before the next one.
8. When I hit a problem, remind me to add it to `docs/notes.md` (problem + solution).

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
- Step 1 files done: `.gitignore` (fixed leading spaces), `requirements.txt` (pinned),
  `pytest.ini`, `.env.example`, `config.py` (key verified to load).
- Next: `git init`, check that `.env` is not in `git status`, create GitHub repo,
  commit `Initial project setup`. Then step 2 (formatting.py).

## Tech stack
- Python 3.14 in a virtual environment (`.venv`)
- `requests` (HTTP), `python-dotenv` (reads `.env`), `pytest` (tests)
- Standard library: `datetime`, `zoneinfo` (Swedish time), `json`
- Note: on Windows, `zoneinfo` needs the `tzdata` package (`pip install tzdata`).

## API facts (Swedavia FlightInfo v2) – verified
- Base URL: `https://api.swedavia.se/flightinfo/v2`
- Headers: `Ocp-Apim-Subscription-Key: <key>` and `Accept: application/json`
- `GET /heartBeat` → `200 OK`, body is the JSON **string** `"IsAlive"` (not an object).
  Optional query param `evaluationId` (we do not use it). Note the capital B.
- `GET /{IATA}/arrivals/{yyyy-mm-dd}` and `GET /{IATA}/departures/{yyyy-mm-dd}` (date in UTC)
- `GET /query?filter=...&count=...&continuationtoken=...` (max 1000 per page; URL-escape the token)
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
- Departures probably mirror this with `from`, `departureTime`, `arrivalAirportEnglish`
  (not verified yet; check with a real response before relying on it).
- `diIndicator`: I = International, D = Domestic.
- `flightLegStatus` `DEL` = deleted/cancelled flight.
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
├── pytest.ini              # pythonpath = .
├── .env                    # SWEDAVIA_API_KEY=...  (never committed)
├── .env.example            # SWEDAVIA_API_KEY=your-key-here
├── .gitignore              # .venv/ .env __pycache__/ .pytest_cache/
├── config.py               # reads the key from .env, BASE_URL, AIRPORTS
├── formatting.py           # fmt_time, is_valid_flight, is_upcoming, print_flight
├── api_client.py           # get(), get_arrivals(), get_departures(), query(), heartbeat()
├── destinations.py         # city → country, destination overview
├── city_country.json
├── airport.py              # main menu (entry point)
├── mock_data/
│   ├── heartbeat_sample.txt   # exists
│   └── arrivals_sample.json   # exists
├── tests/
│   ├── test_formatting.py
│   ├── test_api_client.py  # mocks requests, no real calls
│   └── test_destinations.py
└── docs/
    ├── notes.md            # running log of problems and solutions (exists)
    └── DOCUMENTATION.md    # Phase 1–4 + Conclusion, per the school's guide
```

## Build order
Backend logic with mock data → tests → real API → menu → destinations → docs.
See PLAN.md. Always ask which step we are on before starting.