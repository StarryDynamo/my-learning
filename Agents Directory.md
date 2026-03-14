# Agents Directory

All agents live in `C:\Users\heave\agents\`. This note documents what each one does, how it works, and when it runs.

---

## Midnight Intel

**Path:** `agents\midnight-intel`
**Stack:** Python, Anthropic Claude, Tavily Search, Streamlit

### What it does

The core business intelligence suite for Midnight Labs. Five capabilities:

1. **Account Research** — Generates pre-call intelligence briefs on target companies. Searches the web for L&D signals, AI adoption posture, and leadership profiles, then produces a structured brief with a High/Medium/Low fit assessment.
2. **Signal Monitor** — Scans 10 search queries across APAC for L&D buying signals (CHRO workforce AI readiness, skills gaps, MCP adoption). Scores each signal 1–5 for relevance.
3. **Playbook Builder** — Builds and maintains Midnight Labs' living strategic playbook from internal IP documents. An optimiser agent runs research and proposes updates.
4. **Delivery Playbook Builder** — Generates operational delivery playbooks for each service line: Ecosystem Audit, MCP Pilot, Learning Ecosystem Design, Workforce Data Strategy.
5. **LinkedIn Content** — Generates a week of LinkedIn posts grounded in the playbook, recent signals, and delivery materials. Outputs structured posts with hooks, body, image prompts, and editorial notes.

### How to run

```
cd agents\midnight-intel
python run.py research "Company Name"
python run.py monitor
python run.py build-playbook
python run.py optimise
python run.py build-delivery
python run.py content
streamlit run app.py
```

### Schedule

| Task | Schedule | How |
|---|---|---|
| Playbook optimiser | Weekly, Monday 7:00am | `python run.py optimise --schedule` |
| LinkedIn content | Weekly, Thursday 8:00am | `python run.py content --schedule` |
| Account research | On demand | Manual |
| Signal monitor | On demand | Manual |

### Environment

`.env` requires `ANTHROPIC_API_KEY` and `TAVILY_API_KEY`.

---

## Research Agent

**Path:** `agents\research-agent`
**Stack:** Python, RSS (BeautifulSoup), Semantic Scholar API, Anthropic Claude, Streamlit

### What it does

Scans RSS feeds and academic papers relevant to a Learning Ecosystem Manager role. Sources include Microsoft Copilot, Workday, Cursor, Udemy for Business, OpenAI, MIT Tech Review, TechCrunch, HBR, ATD, and Semantic Scholar queries on workplace learning and human development.

Synthesises all findings into a readable article using Claude and writes it as a markdown note to the Obsidian vault (`Tom's Vault/Research Digest/`).

### How to run

```
cd agents\research-agent
python run_daily_digest.py              # Start daily scheduler (8am Melbourne → vault)
python vault_article.py                 # One-off synthesised article → vault
python vault_article.py --dry-run       # Preview without writing
python scanner.py --vault               # Same via scanner CLI
python scanner.py --out digest.md       # Raw digest to file
streamlit run app.py                    # Interactive UI
```

### Schedule

| Task | Schedule | How |
|---|---|---|
| Vault article | **Daily, 8:00am Melbourne (automated)** | Runs on login via Windows Startup shortcut → `RunDailyVault.vbs` → `pythonw run_daily_digest.py`. Runs silently in the background with no console window. |
| One-off article | On demand | `python vault_article.py` |

### Automation

Starts automatically on Windows login. The process (`pythonw3.11.exe`) runs in the background and checks the clock every 60 seconds. At 8:00am Melbourne time it runs the scan, synthesises via Claude, and writes to the vault.

- **Startup shortcut:** `shell:startup\ResearchAgentDaily.lnk`
- **VBS launcher:** `agents\research-agent\RunDailyVault.vbs`
- **Log file:** `agents\research-agent\daily_digest.log`

To stop: kill the `pythonw3.11.exe` process running `run_daily_digest.py`.
To disable: delete `ResearchAgentDaily.lnk` from `shell:startup`.

### Environment

`.env` requires `ANTHROPIC_API_KEY`.

### Output locations

- **Obsidian:** `Tom's Vault/Research Digest/Research Digest YYYY-MM-DD.md`

---

## Flight Scanner

**Path:** `agents\flight-scanner`
**Stack:** Python, Amadeus Flight Offers API

### What it does

Tracks MEL → KIX (Osaka) airfares. Generates search windows (8 weeks of Fridays × 7/10/14-day trips), fetches the best 5 flights per window from Amadeus ranked by price (40%), duration (35%), and stopovers (25%), and writes results to both a local JSON file and the Obsidian vault.

Currently focused on September/October 2026 departures.

### How to run

```
cd agents\flight-scanner
python fare_scanner.py                  # Full scan → JSON + Obsidian
python fare_scanner.py --price 850      # Record a manually-found best price
```

### Schedule

| Task | Schedule | How |
|---|---|---|
| Fare scan | Weekly (manual) | `python fare_scanner.py` — set up via Task Scheduler if desired |

### Environment

`.env` requires `AMADEUS_CLIENT_ID` and `AMADEUS_CLIENT_SECRET`.

### Output locations

- **Obsidian:** `Tom's Vault/Flight Scanner/Flight Scan YYYY-MM-DD.md`
- **Dashboard:** Open `fare_dashboard.html` in a browser (reads `fare_data.json`)

---

## Meeting Analyser

**Path:** `agents\meeting-analyser`
**Stack:** Python, FastAPI, Ollama (local LLM)

### What it does

Processes Zoom meeting transcripts through a local Ollama model. Generates meeting summaries, extracts action items and tasks, and produces daily reports. Exposed as a REST API.

### How to run

```
cd agents\meeting-analyser
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs at `http://localhost:8000/docs`.

### Schedule

On demand — no automated schedule. Run the API server when needed.

### Environment

Requires Ollama running locally.

---

## NAB AI Coach

**Path:** `agents\nab-ai-coach`
**Stack:** Python (Pipecat, Strands Agents), TypeScript (React client)

### What it does

A real-time voice coaching agent for customer callback practice. Uses text-to-speech and multi-agent orchestration (coach, customer, and employee personas) to simulate coaching conversations. Trained on callback practice guides and radical candour methodology.

### How to run

```
# Server
cd agents\nab-ai-coach\server
pip install -r requirements.txt
python server.py

# Client (separate terminal)
cd agents\nab-ai-coach\client
npm install
npm run dev
```

Client at `http://localhost:5173/`.

### Schedule

On demand — no automated schedule. Interactive voice sessions.

### Environment

`server/.env` — see `server/.env.example` for required keys.

---

## Agents Starter

**Path:** `agents\agents-starter`
**Stack:** Python, Streamlit, Amadeus API, Slack

### What it does

A collection of starter agents built as a learning exercise:

1. **Flights Agent** — MEL ↔ KIX flight monitoring using Amadeus API (precursor to the standalone flight-scanner).
2. **Vendor Intel Agent** — Scans RSS feeds for vendor updates relevant to enterprise L&D tooling.

Both support Slack and email notifications via a shared `common/notify.py` module.

### How to run

```
cd agents\agents-starter
pip install -r requirements.txt    # needs fresh venv after the move
streamlit run app.py               # if there's a UI entry point
```

### Schedule

No automated schedule. Experimental/learning project.

### Environment

`.env` — see `.env.example` for required keys.

---

*Last updated: 2026-03-14*
