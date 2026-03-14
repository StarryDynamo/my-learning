#!/usr/bin/env python3
"""
Research agent scanner: RSS feeds + Semantic Scholar papers.
Tailored for Learning Ecosystem Manager (Copilot, Workday, Cursor, Udemy, human development).
"""
from __future__ import annotations

import datetime as dt
import pathlib
import re
from dataclasses import dataclass, field
from typing import Any

import requests
import yaml
from bs4 import BeautifulSoup
from dateutil import parser as dateparser


@dataclass
class ResearchItem:
    source: str
    category: str  # tooling | ai_tech | human_development
    title: str
    url: str
    published: str
    summary: str
    score: float = 0.0


def load_yaml(path: str | pathlib.Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_rss(url: str, timeout: int = 25) -> list[dict[str, Any]]:
    """Fetch RSS/Atom feed and return list of items (title, url, published, summary)."""
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "xml")
    items = []
    for it in soup.find_all(["item", "entry"]):
        title = (it.title.string or (it.title.text if it.title else "") or "").strip()
        link_tag = it.find("link")
        link = ""
        if link_tag:
            link = link_tag.get("href") or (link_tag.text or "").strip()
        pub = ""
        for tag in ("pubDate", "updated", "published", "dc:date"):
            found = it.find(tag)
            if found and getattr(found, "text", None):
                pub = found.text.strip()
                break
        desc_tag = it.find("description") or it.find("summary")
        summary = (getattr(desc_tag, "text", None) or "") if desc_tag else ""
        if summary:
            summary = re.sub(r"<[^>]+>", " ", summary).strip()[:500]
        items.append({"title": title, "url": link, "published": pub, "summary": summary})
    return items


def fetch_semantic_scholar(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search Semantic Scholar for papers (no API key required for basic use)."""
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": min(limit, 100),
        "fields": "title,url,abstract,year,authors",
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        papers = data.get("data") or []
        out = []
        for p in papers:
            title = p.get("title") or "Untitled"
            link = p.get("url") or f"https://www.semanticscholar.org/paper/{p.get('paperId', '')}"
            year = p.get("year")
            pub = str(year) if year else ""
            abstract = (p.get("abstract") or "")[:500]
            authors = p.get("authors") or []
            auth_str = ", ".join((a.get("name") or "") for a in authors[:3])
            if auth_str:
                summary = f"{auth_str}. {abstract}" if abstract else auth_str
            else:
                summary = abstract
            out.append({
                "title": title,
                "url": link,
                "published": pub,
                "summary": summary,
            })
        return out
    except Exception:
        return []


def simple_score(text: str, pos: list[str], neg: list[str]) -> float:
    t = (text or "").lower()
    score = 0.0
    for w in pos:
        if w and w.lower() in t:
            score += 1.0
    for w in neg:
        if w and w.lower() in t:
            score -= 1.0
    return score


def within_days(iso_or_text: str, days: int) -> bool:
    if not iso_or_text:
        return True
    try:
        d = dateparser.parse(iso_or_text)
    except Exception:
        return True
    if not d:
        return True
    if d.tzinfo:
        now = dt.datetime.now(d.tzinfo)
    else:
        now = dt.datetime.utcnow()
        d = d.replace(tzinfo=None)
        if hasattr(now, "replace"):
            now = (now - now.utcoffset()) if getattr(now, "utcoffset", None) and now.utcoffset() else now
    try:
        delta = (now - d).days
    except TypeError:
        delta = (now.replace(tzinfo=None) - d).days
    return delta <= days


def run_scan(
    sources_path: str | pathlib.Path = "sources.yaml",
    keywords_path: str | pathlib.Path = "keywords.yaml",
    window_days: int = 30,
    min_score: float = 0.0,
    include_papers: bool = True,
    category_filter: list[str] | None = None,
) -> list[ResearchItem]:
    """
    Run full scan: RSS + (optionally) Semantic Scholar.
    category_filter: if set, only include these categories (tooling, ai_tech, human_development).
    """
    sources = load_yaml(sources_path)
    kw = load_yaml(keywords_path)
    pos = kw.get("positive") or []
    neg = kw.get("negative") or []

    collected: list[ResearchItem] = []

    # RSS
    for entry in sources.get("rss_sources") or []:
        name = entry.get("name") or "Unknown"
        category = entry.get("category") or "ai_tech"
        if category_filter and category not in category_filter:
            continue
        url = entry.get("url")
        if not url:
            continue
        try:
            for it in fetch_rss(url):
                if not within_days(it.get("published") or "", window_days):
                    continue
                blob = f"{it.get('title', '')} {it.get('summary', '')}"
                score = simple_score(blob, pos, neg)
                if score >= min_score:
                    collected.append(
                        ResearchItem(
                            source=name,
                            category=category,
                            title=(it.get("title") or "").strip(),
                            url=(it.get("url") or "").strip(),
                            published=(it.get("published") or "").strip(),
                            summary=(it.get("summary") or "").strip(),
                            score=score,
                        )
                    )
        except Exception as e:
            collected.append(
                ResearchItem(
                    source=name,
                    category=category,
                    title=f"[Feed error: {name}]",
                    url=url,
                    published="",
                    summary=str(e),
                    score=0.0,
                )
            )

    # Semantic Scholar (research papers)
    if include_papers:
        for entry in sources.get("semantic_scholar_queries") or []:
            category = entry.get("category") or "human_development"
            if category_filter and category not in category_filter:
                continue
            query = entry.get("query")
            limit = entry.get("limit") or 5
            if not query:
                continue
            try:
                for it in fetch_semantic_scholar(query, limit=limit):
                    blob = f"{it.get('title', '')} {it.get('summary', '')}"
                    score = simple_score(blob, pos, neg)
                    if score >= min_score:
                        collected.append(
                            ResearchItem(
                                source="Semantic Scholar",
                                category=category,
                                title=(it.get("title") or "").strip(),
                                url=(it.get("url") or "").strip(),
                                published=(it.get("published") or "").strip(),
                                summary=(it.get("summary") or "").strip(),
                                score=score,
                            )
                        )
            except Exception:
                pass

    # Sort: tooling first, then by score, then by date
    cat_order = {"tooling": 0, "ai_tech": 1, "human_development": 2}
    collected.sort(
        key=lambda x: (
            cat_order.get(x.category, 99),
            -x.score,
            x.published or "",
        ),
        reverse=False,
    )
    # For date we want newest first where available
    def sort_key(item: ResearchItem) -> tuple:
        try:
            d = dateparser.parse(item.published)
            return (cat_order.get(item.category, 99), -item.score, -(d.timestamp() if d else 0))
        except Exception:
            return (cat_order.get(item.category, 99), -item.score, 0)

    collected.sort(key=sort_key)
    return collected


def format_digest(items: list[ResearchItem]) -> str:
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
    lines = ["# Learning Ecosystem Research Digest\n"]
    lines.append(f"_Generated: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}_\n")
    for cat in ["tooling", "ai_tech", "human_development"]:
        arr = by_cat.get(cat, [])
        if not arr:
            continue
        lines.append(f"## {cat_titles.get(cat, cat)}\n")
        for it in arr[:25]:
            pub = it.published or "—"
            summ = (it.summary or "")[:280] + ("..." if len(it.summary or "") > 280 else "")
            lines.append(f"- **{it.title}**  \n  {summ}  \n  [{it.url}]({it.url})  \n  _Source: {it.source} · {pub}_")
        lines.append("")
    return "\n".join(lines)


def format_digest_for_notebooklm(items: list[ResearchItem]) -> str:
    """Format digest for pasting into Google Docs / NotebookLM — includes intro for podcast context."""
    valid = [i for i in items if not i.title.startswith("[Feed error")]
    if not valid:
        return "Learning Ecosystem Research Digest (no items in this run)."
    intro = (
        "Learning Ecosystem Research Digest — curated for a Learning Ecosystem Manager at a large enterprise. "
        "This digest covers product updates from Copilot, Workday, Cursor, and Udemy for Business; "
        "AI and tech news relevant to L&D; and research on human development and workplace learning. "
        "Use this as the basis for a 20-minute audio overview or podcast.\n\n"
    )
    return intro + format_digest(items)


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Learning Ecosystem Research Agent scanner")
    ap.add_argument("--sources", default="sources.yaml", help="Path to sources.yaml")
    ap.add_argument("--keywords", default="keywords.yaml", help="Path to keywords.yaml")
    ap.add_argument("--days", type=int, default=30, help="Include items from last N days")
    ap.add_argument("--min-score", type=float, default=0.0, help="Minimum relevance score")
    ap.add_argument("--no-papers", action="store_true", help="Skip Semantic Scholar paper search")
    ap.add_argument("--out", default="", help="Write digest to this file (default: stdout)")
    ap.add_argument("--export-notebooklm", metavar="FILE", default="", help="Write digest for NotebookLM (Google Doc / 20-min podcast) to FILE")
    ap.add_argument("--vault", action="store_true", help="Synthesise article via Claude and write to Obsidian vault")
    ap.add_argument("--category", action="append", choices=["tooling", "ai_tech", "human_development"], help="Limit to these categories (can repeat)")
    args = ap.parse_args()

    from dotenv import load_dotenv
    load_dotenv(pathlib.Path(__file__).resolve().parent / ".env")

    category_filter = args.category if args.category else None
    items = run_scan(
        sources_path=args.sources,
        keywords_path=args.keywords,
        window_days=args.days,
        min_score=args.min_score,
        include_papers=not args.no_papers,
        category_filter=category_filter,
    )
    valid_count = len([i for i in items if not i.title.startswith("[Feed error")])

    if args.vault:
        from vault_article import synthesise_article, write_to_vault
        article = synthesise_article(items)
        path = write_to_vault(article)
        print(f"Wrote {path} ({valid_count} items)")
        return

    if args.export_notebooklm:
        pathlib.Path(args.export_notebooklm).parent.mkdir(parents=True, exist_ok=True)
        with open(args.export_notebooklm, "w", encoding="utf-8") as f:
            f.write(format_digest_for_notebooklm(items))
        print(f"Wrote NotebookLM digest to {args.export_notebooklm} ({valid_count} items). See NOTEBOOKLM.md for podcast steps.")
    digest = format_digest(items)
    if args.out:
        pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(digest)
        print(f"Wrote {args.out} with {valid_count} items.")
    elif not args.export_notebooklm:
        print(digest)


if __name__ == "__main__":
    main()
