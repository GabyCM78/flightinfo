# Swedavia FlightInfo – terminal client

A Python terminal app that shows live flight information from Sweden's ten Swedavia airports, using the [Swedavia FlightInfo API v2](https://apideveloper.swedavia.se).

This project is my solution to the APL assignment **"Reverse Engineer a Result"**.
I watched a video of a finished app, worked out how it was built, and rebuilt it with the same features – but safer, more stable, tested and better structured.

## Features

| Menu | What it does | |---|---|
| 1 | **Arrivals** for an airport and a date, 50 flights per page |
| 2 | **Departures** for an airport and a date, 50 flights per page |
| 3 | **Search for a flight number** (e.g. `SK085`) at an airport on a date |
| 4 | **OData query** – write your own filter, e.g. `airport eq 'ARN' and flightType eq 'D'` |
| 5 | **HeartBeat** – is the API up? |
| 6 | **Demo** – calls all four endpoints in a row and shows a short result from each |
| 7 | **Destination overview** – cities with country and number of flights, e.g. `Frankfurt (5 flights) [Germany]` |
| q | Quit |

- Airports can be given as an IATA code or a city name: `ARN`, `arn`, `Visby`, `Göteborg`.
- Dates can be `YYYY-MM-DD`, `today`, `tomorrow`, `yesterday` or `now` (= today, only flights that have not
  landed/departed yet). The Swedish words `idag`, `imorgon`, `igår` and `nu` work too.
- Times are shown in UTC and Swedish time, with summer/winter time handled automatically
  (`20:25 UTC → 22:25 CEST`).
- Deleted "ghost" entries from the API are hidden, and flights are sorted by scheduled time.

## Improvements compared to the original app

| | Original | My version | |---|---|---|
| API key | Hardcoded in the source code | Read from `.env`, never committed to GitHub | | Errors (network, key, input) | Can crash | Clear message, the app never crashes |
| Tests | None visible | 176 pytest tests, no real API calls |
| Structure | Mostly one large file | Small modules with one job each |
| Paging in OData query | Read `continuationToken` (wrong case), so page 2 was probably never fetched | Reads `continuationtoken`, stops correctly, max 5 pages |
| Flight list order | Order from the API | Sorted by scheduled time |
| Destination overview | Separate script that runs once and exits | Menu option 7, everything in one place |

## Requirements

- Python **3.11 or newer** (developed and tested with Python 3.14 on Windows)
- A free API key from the [Swedavia API portal](https://apideveloper.swedavia.se):
  sign up → **Products** → **FlightInfo** → **Subscribe** → copy the *Primary key* from your profile.
  The free tier allows 10,000 requests per month.

## Setup (Windows PowerShell)

```powershell
git clone https://github.com/GabyCM78/flightinfo.git
cd flightinfo
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and replace `your-key-here` with your own key:

```
SWEDAVIA_API_KEY=your-key-here
```

> **Note:** `.env` is listed in `.gitignore`, so the key never ends up on GitHub.
> On Windows with Smart App Control, `pip.exe` and `pytest.exe` inside the venv may be blocked.
> That is why all commands here use `python -m pip` and `python -m pytest`.

On macOS/Linux, use `python3 -m venv .venv`, `source .venv/bin/activate` and `cp .env.example .env` instead.

## Run the app

```powershell
python airport.py
```

Example:

```
Choose: 1
Enter IATA code or city name (e.g. ARN or Visby): Visby
Enter date (YYYY-MM-DD / now / today / tomorrow / yesterday): today
[1] → SK091 | SAS Scandinavian Airlines (SK)
  From : Stockholm ARN
  To   : VBY
  Status   : Landed 06:35
  Terminal : T1   Gate: –
  Baggage  : 01
  Sched : 04:50 UTC → 06:50 CEST
  Est   : 04:34 UTC → 06:34 CEST
  Actual: 04:35 UTC → 06:35 CEST
  D/I   : D
...
── Showing 10/10 ── (0 left)
```

If something goes wrong (wrong key, no network, too many requests, bad input), the app shows a message
such as `⚠ The API key was rejected (401). Check SWEDAVIA_API_KEY in .env.` and returns to the menu.

## Run the tests

```powershell
python -m pytest -v
```

All 176 tests should pass. The tests **never call the real API** and do **not need an API key**:
`requests.get`, `input()`, the clock and the pauses are replaced with fakes, and saved real API responses
in `mock_data/` are used as test data.

## Project structure

```
flightinfo/
├── airport.py            # entry point: the menu, paging (50 per page), demo, destination overview
├── api_client.py         # the only module that talks to the API: get(), heartbeat(), get_arrivals(),
│                         #   get_departures(), query() with paging, build_filter(), ApiError
├── formatting.py         # UTC → Swedish time, ghost-entry filter, upcoming filter, sorting, flight layout
├── user_input.py         # parses what the user types: airport, date, flight number
├── destinations.py       # counts flights per city and looks up the country
├── config.py             # reads the API key from .env, BASE_URL, TIMEOUT, AIRPORTS
├── city_country.json     # 138 cities → country
├── requirements.txt      # pinned versions: requests, python-dotenv, pytest, tzdata
├── pytest.ini
├── .env.example          # template for .env
├── mock_data/            # saved real API responses used by the tests
├── tests/                # pytest tests, one file per module
└── docs/
    ├── DOCUMENTATION.md  # the project report (Phase 1–4 + Conclusion)
    └── notes.md          # my running log of findings, decisions, problems and solutions
```

## Things I found out about the API

These were verified against the real API, not only read in the documentation:

- The date in `/{airport}/arrivals/{date}` is the **Swedish local date**, not UTC.
- The API returns **deleted "ghost" entries** (status `DEL`) with almost no data. They are hidden in the app.
- In `/query`, every flight is **wrapped** in `{"arrival": {...}}` or `{"departure": {...}}`,
  the paging key is `continuationtoken` (lower-case t), and a token is sent **even on the last page**.
- A wrong key gives `401`, an unknown airport gives `400`, and several quick requests can give `429`.

More details are in [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md).
