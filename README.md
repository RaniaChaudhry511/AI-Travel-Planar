# AI Travel Planner Agent

An interactive travel-planning assistant powered by the OpenAI Agents SDK and
Gemini. It can help compare destinations, build itineraries and budget
estimates, check weather and exchange rates, search for current travel
information, remember preferences, and export a plan as a PDF.

## Features

- Suggests destinations using the user's interests, travel style, season,
  dates, companions, preferred weather, and constraints.
- Compares 3–5 countries by budget level, weather, and specialties; explains
  culture, history, best seasons, pros and cons, local customs, and
  Muslim-friendly facilities.
- Plans low-, mid-, or luxury-budget trips in PKR, USD, or another chosen
  currency, with flights, hotels, food, transport, activities, shopping,
  emergency fund, savings tips, and per-day/total estimates.
- Recommends accommodation styles and areas, local dishes, halal/vegetarian
  considerations, attractions, activities, day trips, and family/solo options.
- Creates flexible day-by-day morning-to-night itineraries with travel time,
  meals, rest, and a clean table/timeline.
- Helps research flights, visa/document checklists, airport and local transport,
  SIM/eSIM, weather and packing, safety, health reminders, and emergency
  contacts.
- Provides currency, cash/card, ATM, tipping, bargaining, language phrase, and
  cultural-etiquette guidance.
- Uses tools for live weather, exchange rates, and web search; changing prices,
  schedules, availability, and visa details must be verified with official
  sources.
- Saves budget, food, travel-style, and home-currency preferences locally and
  remembers chat history in SQLite.
- Supports group planning, plan changes, event research, and PDF export through
  the Streamlit chat interface or the responsive web planner.

Live prices, schedules, availability, and visa rules can change. Verify them
with official providers before booking or travel.

## Setup

1. If needed, create the virtual environment from the project root:

   ```powershell
   py -m venv .venv
   ```

2. Install the project requirements with the virtual environment's Python:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root containing `GEMINI_API_KEY` and
   `GEMINI_MODEL`. Do not commit this file.

4. Install or refresh the app dependencies in the virtual environment:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install fastapi uvicorn streamlit duckduckgo-search fpdf2
   ```

## Run

Start the terminal chat:

```powershell
.\.venv\Scripts\python.exe chat.py
```

Start the Streamlit app:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Start the FastAPI web planner:

```powershell
uvicorn server:app --reload
```

Then open <http://127.0.0.1:8000>.

For frontend/backend checks without making Gemini requests, set `MOCK_MODE=1`
before starting the server for a sample plan. To preview quota and temporary
busy error messages, set `MOCK_MODE=quota` or `MOCK_MODE=busy`; these modes
return simulated errors and never call Gemini. In PowerShell:

```powershell
$env:MOCK_MODE = "1"
uvicorn server:app --reload
```

## Deploy to Vercel

Vercel uses the `server:app` entrypoint configured in `pyproject.toml`. The
existing `/static` mount serves the frontend assets; Vercel promotes mounted
`StaticFiles` directories to its CDN. The function timeout is set to 300
seconds in `vercel.json`.

Add `GEMINI_API_KEY` and `GEMINI_MODEL` as Vercel project environment variables
before deploying. On Vercel, chat history and saved preferences use `/tmp`;
this storage is temporary and may reset between function instances or
deployments.

Type `exit` in the terminal chat to quit. The Streamlit sidebar includes
**New trip** and **Download plan as PDF**.

Saved preferences are stored in `user_profile.json`; conversation history is
stored in `travel_history.db`. Both are local project data and are ignored by
Git.
