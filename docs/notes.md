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
- Python 3.14, `requests`, `python-dotenv`, `pytest`
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

---

## Phase 3 – Completion
_(fill in later)_

---

## Improvements compared to the original
| | Original | My version |
|---|---|---|
| API key | Hardcoded in code | `.env`, never on GitHub |
| Errors (network, key, input) | Can crash | Clear message, never crashes |
| Tests | None visible | pytest, no real API calls |
| Structure | Mostly one large file | Small modules, one job each |

---

## Ideas (maybe later)
- ~~Option to hide deleted flights (`DEL`).~~ Done: `is_valid_flight` hides them by default.
- Show "data updated X min ago" using the `last-modified-inminutes` header.