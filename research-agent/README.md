# Learning Ecosystem Research Agent

A research agent that scans **RSS feeds** and **academic papers** (Semantic Scholar) for content relevant to your role as a **Learning Ecosystem Manager** at a large enterprise.

## Focus areas

- **Your tooling:** Microsoft Copilot, Workday, Cursor, Udemy for Business (releases, blogs, product updates).
- **AI & tech:** Broader AI/tech news that affects L&D and learning platforms.
- **Human development:** Latest research in adult learning, workplace learning, L&D effectiveness, and learning ecosystems.

## Quick start

```bash
cd research_agent
pip install -r requirements.txt
streamlit run app.py
```

Open the URL (e.g. http://localhost:8501), choose options in the sidebar, and click **Run scan**.

## Command-line usage

You can run the scanner without the UI and write a digest to a file:

```python
from scanner import run_scan, format_digest

items = run_scan(
    sources_path="sources.yaml",
    keywords_path="keywords.yaml",
    window_days=30,
    include_papers=True,
    category_filter=["tooling", "human_development"],  # optional
)
digest = format_digest(items)
with open("digest.md", "w") as f:
    f.write(digest)
```

From the command line (from the `research_agent` folder):

```bash
python scanner.py --out digest.md
python scanner.py --days 14 --category tooling --category human_development --out digest.md
python scanner.py --no-papers --out rss_only.md
```

## Configuration

- **sources.yaml**  
  - `rss_sources`: list of `name`, `category` (`tooling` | `ai_tech` | `human_development`), and `url`.  
  - `semantic_scholar_queries`: list of `query`, `category`, and `limit` for paper search.

- **keywords.yaml**  
  - `positive`: terms that boost relevance (e.g. learning, skills, copilot, workday).  
  - `negative`: terms that downrank (e.g. off-topic or noise).

Add or remove feeds and queries to match your priorities.

## Data sources

- **RSS:** Microsoft Copilot/365, Workday blog & Medium, Cursor blog & changelog, Udemy blog, Microsoft AI, OpenAI, TechCrunch, MIT Tech Review, HBR, ATD.
- **Papers:** Semantic Scholar (no API key required for basic search). Queries target workplace learning, learning ecosystems, human development, and AI in education.

## Daily digest to Discord (9am Melbourne)

To receive the digest every day at **9:00 AM Melbourne, Australia** time:

1. **Get a Discord webhook URL**
   - Open your **Discord server** → right‑click the **channel** → **Edit Channel** → **Integrations** → **Webhooks** → **New Webhook** → **Copy Webhook URL**.

2. **Configure**
   - In the `research_agent` folder, copy `.env.example` to `.env` and set `DISCORD_WEBHOOK_URL` to that URL.

3. **Run**
   - Post once now: `python discord_daily.py`
   - Daily at 9am Melbourne: run `python run_daily_digest.py` and leave it running (or double‑click `RunDailySlack.bat`).

**Dry run** (scan only, no post): `python discord_daily.py --dry-run`

## Daily digest via GitHub Actions (e.g. my-learning repo)

If **research-agent** lives inside another repo (e.g. **my-learning** with microlearning), GitHub only runs workflows from that repo’s **root**. The workflow inside `research-agent/.github/workflows/` is **not** run.

**Fix:** Add the research workflow at the **repo root**, next to your microlearning workflow:

1. In your **my-learning** repo, ensure you have a folder `.github/workflows/` at the root (same place as `daily-microlearning.yml`).
2. Copy **`research-agent/.github/workflows/daily-research-digest-at-repo-root.yml`** to **`.github/workflows/daily-research-digest.yml`** at the repo root (you can rename when copying).
3. In GitHub: **Settings → Secrets and variables → Actions** → ensure **`ANTHROPIC_API_KEY`** is set.

The workflow runs from the `research-agent/` subfolder and commits a new file each day: `research-agent/outputs/Research Digest YYYY-MM-DD.md` (same naming as the vault). You can sync that folder (or the whole repo) with Obsidian.

## 20-minute podcast via Google NotebookLM

You can feed the digest into **NotebookLM** and generate an AI **Audio Overview** (podcast) of about 20 minutes:

1. Export: `python scanner.py --export-notebooklm digest_for_notebooklm.md`
2. Paste the file contents into a **Google Doc** and add that Doc as a source in [NotebookLM](https://notebooklm.google.com).
3. In NotebookLM, use **Generate audio overview** and choose **Longer** (~20 min).

Full steps and tips: **[NOTEBOOKLM.md](NOTEBOOKLM.md)**.

## Notes

- Some RSS URLs may change; if a feed fails, check the source site for an updated feed URL and edit `sources.yaml`.
- Semantic Scholar rate limits apply; the app uses small limits per query to stay within polite use.
