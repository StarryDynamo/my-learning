#!/usr/bin/env python3
"""Microlearning Generator — Daily knowledge nuggets for your Obsidian vault.

Generates structured microlearning notes using LLM APIs with
spaced repetition, interleaving, and cross-domain bridging.
"""

import json
import os
import random
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).parent


def load_config():
    with open(ROOT / "config.json") as f:
        return json.load(f)


def load_tracker():
    path = ROOT / "learning-tracker.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"history": [], "topic_counts": {}}


def save_tracker(tracker):
    with open(ROOT / "learning-tracker.json", "w") as f:
        json.dump(tracker, f, indent=2)


def set_github_output(**kwargs):
    output_path = os.getenv("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a") as f:
        for key, value in kwargs.items():
            f.write(f"{key}={value}\n")


# ---------------------------------------------------------------------------
# Topic selection — weighted toward least-covered, avoids yesterday's topic
# ---------------------------------------------------------------------------

def select_topic(topics, tracker, override=None):
    if override and override not in ("auto", ""):
        return override

    counts = tracker.get("topic_counts", {})
    for t in topics:
        counts.setdefault(t, 0)

    min_count = min(counts[t] for t in topics)

    candidates, weights = [], []
    for topic in topics:
        candidates.append(topic)
        gap = counts[topic] - min_count
        weights.append(max(1, 10 - gap * 3))

    history = tracker.get("history", [])
    if history and len(candidates) > 1:
        last_topic = history[-1].get("topic")
        for i, t in enumerate(candidates):
            if t == last_topic:
                weights[i] = max(1, weights[i] // 3)

    return random.choices(candidates, weights=weights, k=1)[0]


# ---------------------------------------------------------------------------
# Spaced repetition helpers
# ---------------------------------------------------------------------------

def review_dates_for(today_str, intervals):
    today = datetime.strptime(today_str, "%Y-%m-%d")
    return [(today + timedelta(days=d)).strftime("%Y-%m-%d") for d in intervals]


def concepts_due_for_review(tracker, today_str):
    due = []
    for entry in tracker.get("history", []):
        if today_str in entry.get("review_dates", []):
            due.append(entry)
    return due[-2:]


def recent_concepts(tracker, days=14):
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return [e for e in tracker.get("history", []) if e["date"] >= cutoff]


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def build_daily_prompt(topic, all_topics, recent, reviews):
    other_topics = [t for t in all_topics if t != topic]

    recent_block = ""
    if recent:
        lines = [f"  - {c['topic']}: {c['concept']} ({c['date']})" for c in recent]
        recent_block = (
            "\nPreviously covered (DO NOT repeat these):\n" + "\n".join(lines) + "\n"
        )

    review_block = ""
    if reviews:
        lines = [f"  - {c['topic']}: {c['concept']}" for c in reviews]
        review_block = (
            "\n\nInclude a '## 🔄 Retrieval Challenge' section with 1-2 questions "
            "testing recall of these previously learned concepts:\n"
            + "\n".join(lines)
            + "\n\nFrame questions that require genuine recall. "
            "Put answers in a collapsed section:\n"
            "<details><summary>Check your answers</summary>\n\n"
            "[answers]\n\n</details>\n"
        )

    return f"""Generate a microlearning note on **{topic}**.
{recent_block}
Structure the note EXACTLY as follows:

## 💡 Concept
A single, focused concept in 150-200 words. Choose something specific and
surprising — not a textbook overview. Assume the reader is intelligent but
not a specialist.

## 🔍 Real-World Example
A concrete, specific example (names, dates, details) showing this concept
in action. 100-150 words.

## 🌉 Cross-Domain Bridge
Connect this concept to one of: {', '.join(other_topics)}.
Show how the same principle appears in that other field. 80-120 words.
{review_block}
## 🤔 Reflection Prompt
One thought-provoking question connecting this concept to the reader's own
work or experience.

## 📚 Go Deeper
2-3 specific, real resources (books, papers, talks) for further exploration.

GUIDELINES:
- Choose non-obvious, surprising concepts over textbook basics
- Favor concepts with practical implications
- Write like a brilliant friend sharing something fascinating
- The concept name must be specific (e.g., "The IKEA Effect" not "Cognitive Biases")

Return ONLY the note content, starting with this YAML frontmatter:
---
topic: {topic}
concept: [specific concept name]
date: {datetime.now().strftime("%Y-%m-%d")}
tags: [relevant-tag-1, relevant-tag-2]
connected_topics: [the other domain you bridge to]
---"""


def build_weekly_prompt(week_entries):
    entries_str = "\n".join(
        f"- **{e['topic']}**: {e['concept']} ({e['date']})"
        for e in week_entries
    )
    today = datetime.now().strftime("%Y-%m-%d")
    concepts_csv = ", ".join(e["concept"] for e in week_entries)

    return f"""Create a weekly synthesis note connecting this week's microlearning:

{entries_str}

Structure:

## 🧵 This Week's Thread
200-300 word narrative weaving together the week's concepts. Find hidden
connections and overarching themes.

## 🔗 Key Connections
3-4 bullet points identifying specific cross-domain connections.

## 💭 Synthesis Question
One integrative question that requires combining insights from multiple
concepts this week.

## 🗺️ Knowledge Map
Brief text description of how this week's concepts connect to each other
and to previous weeks' learning.

Return ONLY the note content, starting with YAML frontmatter:
---
type: weekly-synthesis
week_of: {week_entries[0]['date']}
concepts: [{concepts_csv}]
date: {today}
---"""


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------

def call_llm(prompt, config):
    provider = config.get("api_provider", "openai")

    if provider == "anthropic":
        from anthropic import Anthropic

        client = Anthropic()
        resp = client.messages.create(
            model=config.get("model", "claude-sonnet-4-20250514"),
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text

    from openai import OpenAI

    client = OpenAI()
    resp = client.chat.completions.create(
        model=config.get("model", "gpt-4o"),
        max_tokens=2000,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a knowledgeable educator creating microlearning "
                    "content. You write with clarity, depth, and genuine "
                    "intellectual curiosity."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def extract_frontmatter(content, field):
    match = re.search(rf"^{field}:\s*(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip().strip("\"'")
    return None


def slugify(text):
    text = text.lower().replace(" ", "-")
    return re.sub(r"[^a-z0-9-]", "", text)


def write_note(content, topic, today, output_dir):
    concept = extract_frontmatter(content, "concept") or "concept"
    slug = slugify(concept)[:60]
    filename = f"{today}-{slug}.md"

    topic_dir = ROOT / output_dir / topic
    topic_dir.mkdir(parents=True, exist_ok=True)

    filepath = topic_dir / filename
    filepath.write_text(content, encoding="utf-8")
    return str(filepath.relative_to(ROOT)), concept


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def run_daily(config, tracker):
    today = datetime.now().strftime("%Y-%m-%d")
    topics = config["topics"]
    intervals = config.get("spaced_repetition_intervals", [1, 3, 7, 14, 30])
    output_dir = config.get("output_dir", "Microlearning")

    override = os.getenv("TOPIC_OVERRIDE", "auto")
    topic = select_topic(topics, tracker, override)

    recent = recent_concepts(tracker)
    reviews = concepts_due_for_review(tracker, today)
    prompt = build_daily_prompt(topic, topics, recent, reviews)
    content = call_llm(prompt, config)

    filepath, concept = write_note(content, topic, today, output_dir)

    tracker["history"].append({
        "date": today,
        "topic": topic,
        "concept": concept,
        "file": filepath,
        "review_dates": review_dates_for(today, intervals),
    })
    tracker.setdefault("topic_counts", {})
    tracker["topic_counts"][topic] = tracker["topic_counts"].get(topic, 0) + 1
    tracker["last_generated"] = today

    return topic, concept, filepath


def run_weekly(config, tracker):
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = config.get("output_dir", "Microlearning")
    cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    entries = [e for e in tracker.get("history", []) if e["date"] >= cutoff]

    if not entries:
        print("No entries from the past week to synthesize.")
        return None, None, None

    prompt = build_weekly_prompt(entries)
    content = call_llm(prompt, config)

    synth_dir = ROOT / output_dir / "Weekly Synthesis"
    synth_dir.mkdir(parents=True, exist_ok=True)
    filepath = synth_dir / f"{today}-weekly-synthesis.md"
    filepath.write_text(content, encoding="utf-8")

    return "Weekly Synthesis", "Weekly Synthesis", str(filepath.relative_to(ROOT))


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    config = load_config()
    tracker = load_tracker()
    mode = os.getenv("MODE", "daily")

    if mode == "daily":
        if tracker.get("last_generated") == today and not os.getenv("TOPIC_OVERRIDE"):
            print(f"Already generated for {today}. Set TOPIC_OVERRIDE to force.")
            return

        topic, concept, filepath = run_daily(config, tracker)
        save_tracker(tracker)
        print(f"Generated: {concept} ({topic})")
        print(f"Saved to:  {filepath}")
        set_github_output(topic=topic, concept=concept, filepath=filepath)

        synthesis_day = config.get("weekly_synthesis_day", 6)  # 0=Mon … 6=Sun
        if datetime.now().weekday() == synthesis_day:
            print("Also generating weekly synthesis…")
            run_weekly(config, tracker)
            save_tracker(tracker)

    elif mode == "weekly":
        _, _, filepath = run_weekly(config, tracker)
        if filepath:
            save_tracker(tracker)
            print(f"Weekly synthesis saved to: {filepath}")
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
