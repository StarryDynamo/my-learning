#!/usr/bin/env python3
"""
Synthesise research scan results into a readable article using Claude,
then write the article as a markdown note to the Obsidian vault.
"""
from __future__ import annotations

import datetime as dt
import os
import pathlib
import textwrap

from scanner import ResearchItem

# Obsidian vault: set OBSIDIAN_VAULT and optional OBSIDIAN_RESEARCH_FOLDER in env
_DEFAULT_VAULT = pathlib.Path(r"C:\Users\heave\OneDrive\Documents\Tom's Vault")
_raw = os.environ.get("OBSIDIAN_VAULT", "")
VAULT_PATH = pathlib.Path(_raw) if _raw else _DEFAULT_VAULT
VAULT_FOLDER = os.environ.get("OBSIDIAN_RESEARCH_FOLDER", "Research Digest")


def _build_source_block(items: list[ResearchItem]) -> str:
    """Build the raw material Claude will synthesise from."""
    cat_labels = {
        "tooling": "Tooling (Copilot, Workday, Cursor, Udemy)",
        "ai_tech": "AI & Technology",
        "human_development": "Human Development & L&D Research",
    }
    by_cat: dict[str, list[ResearchItem]] = {}
    for it in items:
        if it.title.startswith("[Feed error"):
            continue
        by_cat.setdefault(it.category, []).append(it)

    blocks: list[str] = []
    ref_num = 1
    ref_map: dict[int, ResearchItem] = {}
    for cat in ("tooling", "ai_tech", "human_development"):
        arr = by_cat.get(cat, [])
        if not arr:
            continue
        blocks.append(f"=== {cat_labels.get(cat, cat)} ===")
        for it in arr[:20]:
            summary = (it.summary or "")[:400]
            blocks.append(
                f"[{ref_num}] {it.title}\n"
                f"    Source: {it.source} · {it.published or '—'}\n"
                f"    {summary}\n"
                f"    URL: {it.url}"
            )
            ref_map[ref_num] = it
            ref_num += 1
        blocks.append("")
    return "\n".join(blocks), ref_map


SYSTEM_PROMPT = textwrap.dedent("""\
    You are a senior research analyst writing a weekly intelligence brief for a
    Learning Ecosystem Manager at a large enterprise. Your reader manages
    Copilot, Workday, Cursor, and Udemy for Business.

    Your job is to synthesise the raw items below into a concise, readable
    article (800–1200 words). Structure it as:

    1. **Opening paragraph** – the single most important takeaway this week.
    2. **Tooling updates** – what changed in the platforms they manage and why
       it matters for their roadmap.
    3. **AI & technology** – broader AI/tech developments relevant to L&D
       strategy.
    4. **Human development & research** – new evidence or thinking on how
       people develop through work.
    5. **So what** – 2–3 concrete actions or questions the reader should
       consider this week.

    Rules:
    - Write in clear, direct prose. No bullet lists in the body.
    - Cite sources inline using numbered references like [1], [2] etc.
    - Do NOT invent information beyond what the source material provides.
    - If a category has no items, skip that section.
    - End with a "Sources" section listing each reference number, title, and URL.
""")


def synthesise_article(items: list[ResearchItem]) -> str:
    """Use Claude to synthesise raw items into a readable article."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_article(items)

    try:
        import anthropic
    except ImportError:
        return _fallback_article(items)

    source_block, ref_map = _build_source_block(items)
    if not source_block.strip():
        return "No items found in this scan.\n"

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2500,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Here are the raw items:\n\n{source_block}"}
        ],
    )
    article = response.content[0].text

    return article


def _fallback_article(items: list[ResearchItem]) -> str:
    """Template-based article when no API key is available."""
    valid = [i for i in items if not i.title.startswith("[Feed error")]
    if not valid:
        return "No items found in this scan.\n"

    cat_labels = {
        "tooling": "Tooling Updates",
        "ai_tech": "AI & Technology",
        "human_development": "Human Development & L&D Research",
    }
    by_cat: dict[str, list[ResearchItem]] = {}
    for it in valid:
        by_cat.setdefault(it.category, []).append(it)

    lines = [
        "# Learning Ecosystem Research Digest",
        "",
        f"*{dt.datetime.now().strftime('%A, %d %B %Y')}*",
        "",
    ]

    ref_num = 1
    refs: list[str] = []
    for cat in ("tooling", "ai_tech", "human_development"):
        arr = by_cat.get(cat, [])
        if not arr:
            continue
        lines.append(f"## {cat_labels.get(cat, cat)}")
        lines.append("")
        for it in arr[:15]:
            summary = (it.summary or "")[:300]
            lines.append(f"**{it.title}** [{ref_num}]")
            if summary:
                lines.append(f"{summary}")
            lines.append("")
            refs.append(f"[{ref_num}] {it.title} — {it.source} · {it.published or '—'}  ")
            refs.append(f"{it.url}  ")
            ref_num += 1
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Sources")
    lines.append("")
    lines.extend(refs)

    return "\n".join(lines)


def write_to_vault(article: str, date_str: str | None = None) -> pathlib.Path:
    """Write the article to the Obsidian vault. Returns the file path. Skips write if VAULT_PATH is empty or invalid."""
    if not str(VAULT_PATH).strip() or not VAULT_PATH.exists():
        raise FileNotFoundError(f"Obsidian vault path not set or not found: {VAULT_PATH} (set OBSIDIAN_VAULT)")
    if not date_str:
        date_str = dt.datetime.now().strftime("%Y-%m-%d")

    folder = VAULT_PATH / VAULT_FOLDER
    folder.mkdir(parents=True, exist_ok=True)

    filename = f"Research Digest {date_str}.md"
    filepath = folder / filename

    filepath.write_text(article, encoding="utf-8")
    return filepath


def run_and_write_vault(
    window_days: int = 30,
    include_papers: bool = True,
    min_score: float = 0.0,
    category_filter: list[str] | None = None,
) -> tuple[pathlib.Path, int]:
    """Full pipeline: scan → synthesise → write to vault. Returns (filepath, item_count)."""
    from scanner import run_scan

    dir_ = pathlib.Path(__file__).resolve().parent
    items = run_scan(
        sources_path=dir_ / "sources.yaml",
        keywords_path=dir_ / "keywords.yaml",
        window_days=window_days,
        min_score=min_score,
        include_papers=include_papers,
        category_filter=category_filter,
    )
    valid = [i for i in items if not i.title.startswith("[Feed error")]
    article = synthesise_article(items)
    filepath = write_to_vault(article)
    return filepath, len(valid)


if __name__ == "__main__":
    import argparse
    import sys

    from dotenv import load_dotenv
    load_dotenv(pathlib.Path(__file__).resolve().parent / ".env")

    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="Synthesise research digest → Obsidian vault")
    ap.add_argument("--days", type=int, default=30, help="Include items from last N days")
    ap.add_argument("--no-papers", action="store_true", help="Skip Semantic Scholar")
    ap.add_argument("--min-score", type=float, default=0.0)
    ap.add_argument("--dry-run", action="store_true", help="Print article without writing to vault")
    ap.add_argument("--out", default="", help="Write article to this file instead of vault (creates parent dirs)")
    args = ap.parse_args()

    from scanner import run_scan
    dir_ = pathlib.Path(__file__).resolve().parent
    items = run_scan(
        sources_path=dir_ / "sources.yaml",
        keywords_path=dir_ / "keywords.yaml",
        window_days=args.days,
        min_score=args.min_score,
        include_papers=not args.no_papers,
    )
    valid_count = len([i for i in items if not i.title.startswith("[Feed error")])
    article = synthesise_article(items)

    if args.out:
        out_path = pathlib.Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(article, encoding="utf-8")
        print(f"Wrote {out_path} ({valid_count} items)")
    elif args.dry_run:
        print(article)
        print(f"\n({valid_count} items, dry run — not written to vault)")
    else:
        path = write_to_vault(article)
        print(f"Wrote {path} ({valid_count} items)")
