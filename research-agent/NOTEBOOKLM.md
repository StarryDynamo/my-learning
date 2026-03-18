# Turn Your Research Digest into a 20-Minute NotebookLM Podcast

You can feed the research digest into **Google NotebookLM** and have it generate an **Audio Overview** (AI podcast) of about 20 minutes.

**Want to automate it?** See **[NOTEBOOKLM_AUTOMATION.md](NOTEBOOKLM_AUTOMATION.md)** for what we need from your NotebookLM (Enterprise vs public) to automate adding the digest and generating the podcast.

## Step 1: Export the digest for NotebookLM

From the `research_agent` folder run:

```bash
python scanner.py --export-notebooklm digest_for_notebooklm.md
```

This creates `digest_for_notebooklm.md` with the latest digest plus a short intro so NotebookLM has context for the podcast.

(To limit what’s included: use `--days 14` or `--category tooling --category human_development`.)

## Step 2: Put the digest into a format NotebookLM can use

NotebookLM can use:

- **Google Docs** (recommended): Create a new Google Doc, paste in the full contents of `digest_for_notebooklm.md`, and save.  
  - To open the file: `start digest_for_notebooklm.md` (Windows) or open it in any text editor, then copy all and paste into the Doc.

- **Plain text**: You can also paste the same text directly into NotebookLM when adding a source, if your version of NotebookLM supports pasted text.

## Step 3: Add the source in NotebookLM

1. Go to [NotebookLM](https://notebooklm.google.com) and open or create a notebook.
2. Click **Add source** (or **+**).
3. Choose **Google Drive** and select the Google Doc you created (or use **Upload** if you exported a PDF).
4. Wait until the source is processed.

## Step 4: Generate a ~20-minute Audio Overview

1. In the notebook, open the **Audio Overview** / **Generate audio overview** option.
2. Pick **Longer** (about **20 minutes**) when asked for length.  
   - If you only see “Deep Dive” / “Brief” etc., choose **Deep Dive** for a longer, in-depth conversation.
3. Optionally add a **custom prompt**, for example:  
   *“Host a 20-minute podcast for a Learning Ecosystem Manager. Cover product updates (Copilot, Workday, Cursor, Udemy), AI and L&D trends, and human development research. Two hosts, conversational tone.”*
4. Click **Generate** and wait. NotebookLM will produce an AI-hosted podcast from your digest.

## Tips

- **Longer podcasts**: Add more content (e.g. paste multiple digest exports into one Doc, or add several Docs as sources). People have made 30–60+ minute overviews with enough material.
- **Focused episode**: Export with fewer categories, e.g.  
  `python scanner.py --export-notebooklm tooling_only.md --category tooling`  
  then use that Doc for a shorter, tooling-focused episode.
- **Regular episodes**: Re-run the export (e.g. weekly), create a new Doc or update the same one, and generate a new Audio Overview each time.

## References

- [NotebookLM – Add sources](https://support.google.com/notebooklm/answer/16215270) (Docs, PDFs, paste, etc.)
- [NotebookLM – Generate Audio Overview](https://support.google.com/notebooklm/answer/16212820) (length options and formats)
