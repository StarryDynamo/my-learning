"""
Streamlit UI for the Learning Ecosystem Research Agent.
Run: streamlit run app.py
"""
import pathlib

import streamlit as st

from scanner import run_scan, format_digest, ResearchItem

st.set_page_config(
    page_title="Learning Ecosystem Research Agent",
    page_icon="📚",
    layout="wide",
)

DIR = pathlib.Path(__file__).resolve().parent
SOURCES = DIR / "sources.yaml"
KEYWORDS = DIR / "keywords.yaml"

st.title("📚 Learning Ecosystem Research Agent")
st.caption(
    "Scans RSS feeds and research papers relevant to your role: **Copilot**, **Workday**, **Cursor**, **Udemy for Business**, "
    "and latest in AI/tech and human development research."
)

with st.sidebar:
    st.header("Scan options")
    window_days = st.slider("Include items from last (days)", 7, 90, 30)
    min_score = st.number_input("Minimum relevance score", 0.0, 10.0, 0.0, 0.5)
    include_papers = st.checkbox("Include research papers (Semantic Scholar)", value=True)
    categories = st.multiselect(
        "Categories",
        ["tooling", "ai_tech", "human_development"],
        default=["tooling", "ai_tech", "human_development"],
        help="Tooling = Copilot, Workday, Cursor, Udemy. Human development = L&D and learning science research.",
    )
    run = st.button("Run scan", type="primary")

if run:
    category_filter = categories if categories else None
    with st.spinner("Scanning RSS feeds and research papers…"):
        try:
            results = run_scan(
                sources_path=SOURCES,
                keywords_path=KEYWORDS,
                window_days=window_days,
                min_score=min_score,
                include_papers=include_papers,
                category_filter=category_filter,
            )
            st.session_state["results"] = results
            st.session_state["digest"] = format_digest(results)
        except Exception as e:
            st.error(f"Scan failed: {e}")
            st.session_state["results"] = []
            st.session_state["digest"] = ""

results: list[ResearchItem] = st.session_state.get("results", [])
digest: str = st.session_state.get("digest", "")

if not run and not results:
    st.info("Click **Run scan** in the sidebar to fetch the latest from your tooling (Copilot, Workday, Cursor, Udemy), AI/tech, and human development research.")
    st.stop()

# Filter out feed errors for count
valid = [r for r in results if not r.title.startswith("[Feed error")]

st.metric("Items found", len(valid))

if not valid:
    st.info("No items matched your filters. Try lowering the minimum score or increasing the time window.")
else:
    tab_digest, tab_list, tab_markdown = st.tabs(["Digest", "List", "Markdown"])

    with tab_digest:
        st.markdown(digest)

    with tab_list:
        by_cat = {}
        for r in valid:
            by_cat.setdefault(r.category, []).append(r)
        for cat in ["tooling", "ai_tech", "human_development"]:
            arr = by_cat.get(cat, [])
            if not arr:
                continue
            st.subheader(cat.replace("_", " ").title())
            for r in arr:
                with st.expander(f"{r.title[:80]}{'…' if len(r.title) > 80 else ''}"):
                    st.caption(f"Source: {r.source} · {r.published}")
                    if r.summary:
                        st.write(r.summary)
                    st.link_button("Open", r.url)
            st.divider()

    with tab_markdown:
        st.code(digest, language="markdown")
        st.download_button(
            "Download digest (.md)",
            data=digest,
            file_name=f"learning_ecosystem_digest_{pathlib.Path(__file__).parent.name}.md",
            mime="text/markdown",
        )

st.sidebar.divider()
st.sidebar.caption(
    "Sources: RSS feeds for Copilot, Workday, Cursor, Udemy, HBR, ATD, tech blogs; "
    "Semantic Scholar for L&D and human development papers. Edit sources.yaml to add or remove feeds."
)
