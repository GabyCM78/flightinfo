# Project notes – Swedavia FlightInfo

Running log of findings, problems, and solutions.
This is the raw material for DOCUMENTATION.md and the video.

---

## Phase 1 – Research

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
  - `flightLegStatus: "DEL"` = deleted/cancelled flight.
  - `diIndicator`: I = International, D = Domestic.
  - 365 flights in one day explains why the original uses paging.
- Saved sample responses in `mock_data/` to use in tests.

### Tools chosen
- Python 3.14, `requests`, `python-dotenv`, `pytest`
- VS Code + Claude as a coding assistant (asks before every change)
- Git + GitHub

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
- Option to hide deleted flights (`DEL`).
- Show "data updated X min ago" using the `last-modified-inminutes` header.