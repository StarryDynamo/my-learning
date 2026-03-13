# Microlearning Agent

Automated daily microlearning delivered to your Obsidian vault. Each morning, a GitHub Actions workflow generates a structured note on one of your chosen topics and commits it to this repo. Obsidian Git syncs it to your vault automatically.

## Topics

- Learning Science / Learning Ecosystems
- Behavioural Economics
- Complexity Theory
- AI Management
- Strategy

## How it works

```
6:00 AM UTC (daily cron)          You tap "Run" in GitHub Mobile
        │                                   │
        └──────────┬────────────────────────┘
                   ▼
           GitHub Actions
                   │
        ┌──────────┼──────────────┐
        ▼          ▼              ▼
  Read tracker   Pick topic   Get review items
        │          │              │
        └──────────┼──────────────┘
                   ▼
          Call LLM API (generate note)
                   ▼
          Commit .md + update tracker
                   ▼
          Obsidian Git pulls → note appears in vault
```

Each note includes:

| Section | Learning Science Purpose |
|---|---|
| Concept | One focused idea, 150-200 words (chunking) |
| Real-World Example | Concrete application (dual coding) |
| Cross-Domain Bridge | Connection to another topic (interleaving, transfer) |
| Retrieval Challenge | Question on a past concept (spaced repetition) |
| Reflection Prompt | Personal connection (elaborative interrogation) |
| Go Deeper | 2-3 real resources for further reading |

## Setup

### 1. Add your LLM API key as a GitHub secret

Go to [your repo settings](https://github.com/StarryDynamo/my-learning/settings/secrets/actions) → **New repository secret**.

**If using OpenAI (default):**
- Name: `OPENAI_API_KEY`
- Value: your OpenAI API key

**If using Anthropic:**
- Name: `ANTHROPIC_API_KEY`
- Value: your Anthropic API key
- Also update `config.json`: set `api_provider` to `"anthropic"` and `model` to `"claude-sonnet-4-20250514"`

### 2. Set up Obsidian Git (desktop)

1. In Obsidian, go to **Settings → Community Plugins → Browse**
2. Search for **Obsidian Git** and install it
3. Clone this repo into your vault folder (or use it as the vault):
   ```bash
   cd /path/to/your/vault
   git clone https://github.com/StarryDynamo/my-learning.git
   ```
4. In Obsidian Git settings, set **Auto pull interval** to `10` minutes

### 3. Set up Obsidian Git (mobile)

1. Install **Obsidian Git** on Obsidian Mobile
2. Configure it to pull from the same repo
3. New notes will sync automatically when you open Obsidian

### 4. Trigger from your phone

**Option A: GitHub Mobile app**
1. Install the GitHub app on your phone
2. Navigate to your repo → **Actions** → **Daily Microlearning**
3. Tap **Run workflow** → choose topic or leave as "auto"

**Option B: iOS Shortcut (advanced)**

Create a shortcut that calls the GitHub API:

```
POST https://api.github.com/repos/StarryDynamo/my-learning/actions/workflows/daily-microlearning.yml/dispatches
Headers: Authorization: Bearer YOUR_GITHUB_TOKEN
Body: {"ref": "main", "inputs": {"mode": "daily", "topic": "auto"}}
```

### 5. Adjust the schedule

The cron runs at **6:00 AM UTC** by default. Edit `.github/workflows/daily-microlearning.yml` and change the cron expression to match your timezone:

| Timezone | Cron for 7 AM local |
|---|---|
| UTC | `0 7 * * *` |
| UK (GMT/BST) | `0 7 * * *` (winter) / `0 6 * * *` (summer) |
| US Eastern | `0 12 * * *` |
| US Pacific | `0 15 * * *` |
| AEST | `0 21 * * *` (previous day UTC) |

## Configuration

Edit `config.json` to customize:

```json
{
  "topics": ["Learning Science", "Behavioural Economics", ...],
  "api_provider": "openai",        // or "anthropic"
  "model": "gpt-4o",               // or "claude-sonnet-4-20250514"
  "output_dir": "Microlearning",
  "spaced_repetition_intervals": [1, 3, 7, 14, 30],
  "weekly_synthesis_day": 6        // 0=Monday ... 6=Sunday
}
```

### Adding or changing topics

Edit the `topics` array in `config.json`. The system adapts automatically — no other changes needed.

## Manual generation

You can also run the script locally:

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
python generate.py
```

Override the topic:
```bash
TOPIC_OVERRIDE="Strategy" python generate.py
```

Force weekly synthesis:
```bash
MODE=weekly python generate.py
```

## Vault structure

```
Microlearning/
├── Learning Science/
│   └── 2026-03-14-the-testing-effect.md
├── Behavioural Economics/
│   └── 2026-03-15-the-ikea-effect.md
├── Complexity Theory/
│   └── 2026-03-16-the-adjacent-possible.md
├── AI Management/
│   └── 2026-03-17-centaur-chess.md
├── Strategy/
│   └── 2026-03-18-wardley-mapping.md
└── Weekly Synthesis/
    └── 2026-03-20-weekly-synthesis.md
```
