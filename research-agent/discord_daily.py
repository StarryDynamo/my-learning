#!/usr/bin/env python3
"""
Run the research scan and post the digest to Discord (daily 9am Melbourne update).
Set DISCORD_WEBHOOK_URL in .env. Run manually or via run_daily_digest.py scheduler.
"""
from __future__ import annotations

import json
import os
import pathlib
import urllib.request

from dotenv import load_dotenv

from scanner import run_scan, format_digest, ResearchItem

DIR = pathlib.Path(__file__).resolve().parent
SOURCES = DIR / "sources.yaml"
KEYWORDS = DIR / "keywords.yaml"

DISCORD_CHUNK_CHARS = 1900  # Discord message limit 2000


def format_digest_for_discord(items: list[ResearchItem]) -> list[str]:
    """Format digest as one or more Discord messages (Markdown). Max 2000 chars each."""
    by_cat: dict[str, list[ResearchItem]] = {}
    for it in items:
        if it.title.startswith("[Feed error"):
            continue
        by_cat.setdefault(it.category, []).append(it)
    cat_titles = {
        "tooling": "🛠 Your tooling (Copilot, Workday, Cursor, Udemy)",
        "ai_tech": "🤖 AI & tech",
        "human_development": "📚 Human development & L&D research",
    }
    messages: list[str] = []
    for cat in ["tooling", "ai_tech", "human_development"]:
        arr = by_cat.get(cat, [])
        if not arr:
            continue
        block = [f"**{cat_titles.get(cat, cat)}**"]
        for it in arr[:20]:
            summ = (it.summary or "")[:150] + ("..." if len(it.summary or "") > 150 else "")
            block.append(f"• **{it.title}**\n  {summ}\n  [Open]({it.url}) · {it.source}")
        chunk = "\n\n".join(block)
        if len(chunk) <= DISCORD_CHUNK_CHARS:
            messages.append(chunk)
        else:
            messages.append(f"**{cat_titles.get(cat, cat)}**")
            current = ""
            for it in arr[:20]:
                line = f"• **{it.title}**\n  [Open]({it.url}) · {it.source}\n"
                if len(current) + len(line) > DISCORD_CHUNK_CHARS and current:
                    messages.append(current)
                    current = line
                else:
                    current = current + ("\n" if current else "") + line
            if current:
                messages.append(current)
    return messages


def post_to_discord(webhook_url: str, content: str) -> tuple[bool, str | None]:
    """Post one message to Discord via Webhook. Content max 2000 chars."""
    if not webhook_url:
        return False, "Missing Discord webhook URL"
    if len(content) > 2000:
        content = content[:1997] + "..."
    payload = {"content": content}
    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "ResearchAgent/1.0 (Discord Webhook)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        return True, None
    except Exception as e:
        return False, str(e)


def run_and_post(
    webhook_url: str | None = None,
    window_days: int = 30,
    include_papers: bool = True,
) -> tuple[bool, str]:
    """Run the scan and post the digest to Discord. Returns (success, message)."""
    load_dotenv(DIR / ".env")
    url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
    if not url:
        return False, "Set DISCORD_WEBHOOK_URL in .env (or pass webhook_url=...)."

    items = run_scan(
        sources_path=SOURCES,
        keywords_path=KEYWORDS,
        window_days=window_days,
        min_score=0.0,
        include_papers=include_papers,
        category_filter=None,
    )
    valid = [i for i in items if not i.title.startswith("[Feed error")]
    now = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")

    if not valid:
        header = "📚 **Learning Ecosystem Research Digest**\nNo new items in the last {} days.".format(window_days)
        ok, err = post_to_discord(url, header)
        return (True, "Posted (empty digest).") if ok else (False, err or "Failed to post.")

    header = "📚 **Learning Ecosystem Research Digest** · {} items · {}".format(len(valid), now)
    ok1, err1 = post_to_discord(url, header)
    if not ok1:
        return False, err1 or "Failed to post header."

    for msg in format_digest_for_discord(items):
        ok, err = post_to_discord(url, msg)
        if not ok:
            return False, err or "Failed to post section."
    return True, "Posted to Discord (header + {} sections).".format(len(format_digest_for_discord(items)))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Run research scan and post digest to Discord")
    ap.add_argument("--days", type=int, default=30, help="Include items from last N days")
    ap.add_argument("--no-papers", action="store_true", help="Skip Semantic Scholar")
    ap.add_argument("--dry-run", action="store_true", help="Run scan and print digest only, do not post")
    args = ap.parse_args()

    load_dotenv(DIR / ".env")
    if args.dry_run:
        import sys
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        items = run_scan(
            sources_path=SOURCES,
            keywords_path=KEYWORDS,
            window_days=args.days,
            include_papers=not args.no_papers,
        )
        print(format_digest(items))
        print("\n(Dry run: not posting to Discord)")
    else:
        ok, msg = run_and_post(window_days=args.days, include_papers=not args.no_papers)
        if ok:
            print(msg)
        else:
            print("Error:", msg)
            exit(1)
