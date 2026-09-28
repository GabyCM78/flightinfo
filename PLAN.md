# Plan – Swedavia FlightInfo (klart torsdag)

**Mål:** samma app som Swedavia-originalet (alla funktioner), men förbättrad:
1. **Säkerhet:** API-nyckeln ligger i `.env`, inte i koden
2. **Stabilitet:** felhantering, så att appen aldrig kraschar
3. **Tester** med pytest
4. **Ren struktur:** små filer i stället för en stor

Varje steg: **be Claude om en plan → godkänn → Claude kodar → förstå → testa → commit.**
Claude ger dig alltid numrerade steg för vad du själv ska göra, ett i taget.
Prompterna nedan kan du klistra in i Claude i VS Code.

---

## Steg 0 – API-nyckel (idag, ca 10 min)
1. Gå till https://apideveloper.swedavia.se och klicka **Sign up**. Registrera dig och bekräfta via mejlet.
2. Gå till **Products** → **FlightInfo** → **Subscribe** (gratis, 10 000 anrop/månad).
3. Gå till **Profile** → din prenumeration → **Show** vid *Primary key* och kopiera den.
4. Leta i portalen under **APIs → FlightInfo** efter exakt sökväg för HeartBeat/health och notera den.
5. Testa nyckeln direkt i portalen med **Try it** (t.ex. ARN arrivals idag). Du ska få 200 och JSON.
6. Spara ett exempelsvar: kopiera JSON-svaret till en fil. Det blir din mockdata i steg 2.

**Klart när:** du har en nyckel, har sett ett riktigt JSON-svar och sparat det.

---

## Steg 1 – Setup (mån)
> "Läs CLAUDE.md. Vi är på steg 1. Föreslå hur vi skapar projektmappen, .venv, requirements.txt, pytest.ini, .gitignore, .env.example och config.py. Visa planen innan du gör något."

- Du skapar ett repo på GitHub och kör `git init` enligt skolans guide.
- Kontrollera att `.env` **inte** syns i `git status`.

**Commit:** `Initial project setup`

---

## Steg 2 – Backend-logik med mockdata (mån–tis)
> "Steg 2. Vi bygger formatting.py en funktion i taget, med mock_data/arrivals_sample.json. Börja med fmt_time. Förklara vad, varför, hur."

Ordning: `fmt_time` → `is_valid_flight` → `is_upcoming` → `print_flight`.

Förstå: varför UTC → svensk tid (`zoneinfo`), vad en "spökpost" är.

**Commit per funktion**, t.ex. `Add fmt_time with UTC to Swedish time conversion`

---

## Steg 3 – Tester (tis)
> "Steg 3. Skriv pytest-tester för formatting.py. Förklara varje test. Inga riktiga API-anrop."

- Kör `pytest -v`. Alla tester ska vara gröna.
- Testa gärna specialfall: tom tid, "N/A", sommartid (CEST) och vintertid (CET).

**Commit:** `Add tests for formatting helpers`

---

## Steg 4 – Koppla på API:t (tis–ons)
> "Steg 4. Bygg api_client.py stegvis: först get() och heartbeat(), sedan get_arrivals/get_departures, sist query() med continuationToken. Skriv tester med mockade requests."

Ordning och kontroll:
1. `heartbeat()` → kör manuellt och se att du får svar
2. `get_arrivals("ARN", idag)` → skriv ut 3 flyg
3. `get_departures(...)`
4. `query(...)` med paginering

**Förbättring (stabilitet):** testa medvetet att det går fel, och se att appen visar ett tydligt meddelande:
- fel nyckel i `.env` → 401
- fel flygplats, t.ex. "XXX"
- stäng av wifi → inget nät / timeout

Skriv tester för varje felfall, med mockade svar. Anteckna i `docs/notes.md` hur originalet hanterade detta jämfört med din version.

**Commit per endpoint.**

---

## Steg 5 – Meny och destinationer (ons)
> "Steg 5. Bygg airport.py med menyn 1–6 + q och paginering 50 åt gången. Sedan destinations.py med city_country.json."

- Menyval: ankomster, avgångar, sök flightnummer, query, heartbeat, demo
- Flygplats kan anges som IATA-kod eller stadsnamn, och datum som idag/imorgon/igår/YYYY-MM-DD
- `city_country.json`: börja litet (ca 20 städer), det räcker för att visa idén

**Commit:** `Add interactive menu` och `Add destination overview`

---

## Steg 6 – Dokumentation och video (ons–tors, på engelska)
> "Steg 6. Hjälp mig skriva README.md och docs/DOCUMENTATION.md enligt faserna i skolans guide. Använd mina anteckningar om problem och lösningar."

**DOCUMENTATION.md:** Phase 1 Research · Phase 2 Implementation · Phase 3 Completion · Phase 4 Problems & Solutions · Conclusion

**Video (minst 4 min):** syfte → research (visa originalappen och dina gissningar) → hur du byggde → tester (`pytest -v`) → körning live → problem och lösningar → vad du lärt dig.

💡 **Anteckna problem direkt när de händer** (t.ex. i `docs/notes.md`). Det är det viktigaste i dokumentationen.

Redan ett bra exempel: *Problem:* originalappen hade API-nyckeln i koden. *Lösning:* `.env` + `.gitignore`.

**Lägg till en jämförelsetabell i dokumentationen och visa den i videon:**
| | Original | Min version |
|---|---|---|
| API-nyckel | Hårdkodad i koden | `.env`, aldrig på GitHub |
| Fel (nät, nyckel, indata) | Kan krascha | Tydligt meddelande, kraschar inte |
| Tester | Inga synliga | pytest, körs utan riktiga API-anrop |
| Struktur | Nästan allt i en stor fil (`airport.py`) | Små moduler med ett ansvar var |

---

## Reverse engineering-kopplingen (för rapporten)
| Uppgiftens steg | Vad du gjorde |
|---|---|
| 1. Look at the application | Såg videon: terminalapp, meny, flygdata |
| 2. Ask questions | Vilken data? → Swedavia FlightInfo API v2 |
| 3. Guess the inputs | Flygplats (IATA), datum, flightnummer, filter |
| 4. Guess the process | Anrop → JSON → filtrera → formatera tid → skriv ut sida för sida |
| 5. Sketch the steps | Pseudokod för varje funktion (steg 2) |
| 6. Try building it | Din app + tester |
