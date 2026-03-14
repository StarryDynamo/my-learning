#!/usr/bin/env python3
"""Morning Briefing Generator — one note that combines all agent outputs.

Reads today's microlearning note, research digest, flight scanner updates,
and spaced repetition schedule, then produces a concise morning briefing.
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).parent


def find_latest_file(directory, pattern, max_age_days=2):
    """Find the most recent file matching a glob pattern."""
    target = ROOT / directory
    if not target.exists():
        return None
    matches = sorted(target.rglob(pattern), reverse=True)
    if not matches:
        return None
    return matches[0]


def read_file_safe(path, max_chars=3000):
    if not path or not path.exists():
        return None
    try:
        content = path.read_text(encoding="utf-8")
        return content[:max_chars]
    except Exception:
        return None


def get_todays_microlearning(today):
    """Find today's microlearning note."""
    ml_dir = ROOT / "Microlearning"
    if not ml_dir.exists():
        return None, None

    for topic_dir in ml_dir.iterdir():
        if not topic_dir.is_dir():
            continue
        for f in topic_dir.glob(f"{today}-*.md"):
            content = read_file_safe(f)
            topic = topic_dir.name
            concept = f.stem.replace(f"{today}-", "").replace("-", " ").title()
            fm_match = re.search(r"^concept:\s*(.+)$", content or "", re.MULTILINE)
            if fm_match:
                concept = fm_match.group(1).strip().strip("\"'")
            return {
                "topic": topic,
                "concept": concept,
                "path": str(f.relative_to(ROOT)),
                "content": content,
            }, content
    return None, None


def get_todays_digest(today):
    """Find today's research digest."""
    path = ROOT / "Research Digest" / f"Research Digest {today}.md"
    content = read_file_safe(path)
    if content:
        return {"path": str(path.relative_to(ROOT)), "content": content}
    yesterday = (datetime.strptime(today, "%Y-%m-%d") - timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )
    path = ROOT / "Research Digest" / f"Research Digest {yesterday}.md"
    content = read_file_safe(path)
    if content:
        return {"path": str(path.relative_to(ROOT)), "content": content}
    return None


def get_latest_flight_scan():
    """Find the most recent flight scanner note."""
    scan_dir = ROOT / "Flight Scanner"
    if not scan_dir.exists():
        return None
    scans = sorted(scan_dir.glob("Flight Scan *.md"), reverse=True)
    if not scans:
        return None
    latest = scans[0]
    age = (datetime.now() - datetime.fromtimestamp(latest.stat().st_mtime)).days
    if age > 7:
        return None
    return {
        "path": str(latest.relative_to(ROOT)),
        "content": read_file_safe(latest, max_chars=1500),
        "age_days": age,
    }


def get_review_items(today):
    """Check the learning tracker for concepts due for review today."""
    tracker_path = ROOT / "learning-tracker.json"
    if not tracker_path.exists():
        return []
    try:
        tracker = json.loads(tracker_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    due = []
    for entry in tracker.get("history", []):
        if today in entry.get("review_dates", []):
            due.append(entry)
    return due


def build_briefing_prompt(today, microlearning, digest, flight, reviews):
    date_display = datetime.strptime(today, "%Y-%m-%d").strftime("%A, %d %B %Y")

    sections = []
    sections.append(
        f"Create a morning briefing note for {date_display}. "
        "Be concise and energising — this is a 2-minute read to start the day.\n"
    )

    if microlearning:
        sections.append(
            f"TODAY'S MICROLEARNING:\n"
            f"Topic: {microlearning['topic']}\n"
            f"Concept: {microlearning['concept']}\n"
            f"File: {microlearning['path']}\n"
            f"Content excerpt:\n{microlearning['content'][:1200]}\n"
        )

    if digest:
        sections.append(
            f"TODAY'S RESEARCH DIGEST:\n"
            f"File: {digest['path']}\n"
            f"Content excerpt:\n{digest['content'][:1500]}\n"
        )

    if flight:
        sections.append(
            f"LATEST FLIGHT SCAN ({flight['age_days']} day(s) ago):\n"
            f"File: {flight['path']}\n"
            f"Content excerpt:\n{flight['content'][:800]}\n"
        )

    if reviews:
        review_lines = [f"  - {r['topic']}: {r['concept']}" for r in reviews]
        sections.append(
            "SPACED REPETITION — concepts due for review today:\n"
            + "\n".join(review_lines)
        )

    sections.append(f"""
Structure the briefing EXACTLY as follows:

---
type: morning-briefing
date: {today}
---

# ☀️ Morning Briefing — {date_display}

## 🧠 Today's Learning
A 2-3 sentence summary of today's microlearning concept and why it matters.
Include an Obsidian link: [[{microlearning['path'].replace('.md', '') if microlearning else ''}]]

## 📰 Research Highlights
3-4 key takeaways from today's research digest in bullet points.
Include an Obsidian link: [[{digest['path'].replace('.md', '') if digest else ''}]]

{"## ✈️ Flight Watch" + chr(10) + "Brief summary of the latest fare scan." if flight else ""}

{"## 🔄 Review Due" + chr(10) + "List concepts due for spaced repetition review today with a brief recall prompt for each." if reviews else ""}

## 🎯 Today's Thread
One sentence connecting today's microlearning and research themes — what's the throughline?

GUIDELINES:
- Be concise, warm, and energising
- Use Obsidian [[wikilinks]] for cross-references
- No fluff — every sentence should earn its place
""")

    return "\n\n".join(sections)


def call_llm(prompt):
    provider = os.getenv("API_PROVIDER", "openai")

    if provider == "anthropic":
        from anthropic import Anthropic

        client = Anthropic()
        resp = client.messages.create(
            model=os.getenv("MODEL", "claude-sonnet-4-20250514"),
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text

    from openai import OpenAI

    client = OpenAI()
    resp = client.chat.completions.create(
        model=os.getenv("MODEL", "gpt-4o"),
        max_tokens=1500,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a personal briefing assistant. You write concise, "
                    "warm, and energising morning summaries that help the reader "
                    "start their day informed and focused."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content


def build_fallback_briefing(today, microlearning, digest, flight, reviews):
    """Template-based briefing when no LLM API is available."""
    date_display = datetime.strptime(today, "%Y-%m-%d").strftime("%A, %d %B %Y")
    lines = [
        "---",
        "type: morning-briefing",
        f"date: {today}",
        "---",
        "",
        f"# ☀️ Morning Briefing — {date_display}",
        "",
    ]

    if microlearning:
        lines.extend([
            "## 🧠 Today's Learning",
            f"**{microlearning['concept']}** ({microlearning['topic']})",
            f"→ [[{microlearning['path'].replace('.md', '')}|Read full note]]",
            "",
        ])

    if digest:
        lines.extend([
            "## 📰 Research Digest",
            f"→ [[{digest['path'].replace('.md', '')}|Read full digest]]",
            "",
        ])

    if flight:
        lines.extend([
            "## ✈️ Flight Watch",
            f"Latest scan: {flight['age_days']} day(s) ago",
            f"→ [[{flight['path'].replace('.md', '')}|View scan]]",
            "",
        ])

    if reviews:
        lines.append("## 🔄 Review Due")
        for r in reviews:
            lines.append(f"- **{r['concept']}** ({r['topic']})")
        lines.append("")

    return "\n".join(lines)


def main():
    today = datetime.now().strftime("%Y-%m-%d")

    microlearning, _ = get_todays_microlearning(today)
    digest = get_todays_digest(today)
    flight = get_latest_flight_scan()
    reviews = get_review_items(today)

    if not microlearning and not digest:
        print(f"No microlearning or research content found for {today}. Skipping.")
        return

    has_api = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

    if has_api:
        prompt = build_briefing_prompt(today, microlearning, digest, flight, reviews)
        content = call_llm(prompt)
    else:
        content = build_fallback_briefing(today, microlearning, digest, flight, reviews)

    briefing_dir = ROOT / "Morning Briefing"
    briefing_dir.mkdir(parents=True, exist_ok=True)
    filepath = briefing_dir / f"{today}-morning-briefing.md"
    filepath.write_text(content, encoding="utf-8")

    print(f"Morning briefing saved to: {filepath.relative_to(ROOT)}")

    gh_output = os.getenv("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a") as f:
            f.write(f"filepath={filepath.relative_to(ROOT)}\n")


if __name__ == "__main__":
    main()
