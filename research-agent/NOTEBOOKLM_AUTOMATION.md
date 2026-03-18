# What We Need From Your NotebookLM to Automate the Podcast

It depends which version of NotebookLM you use.

---

## Option A: NotebookLM Enterprise (Google Cloud) — full automation

If your organization has **NotebookLM Enterprise** (via Google Cloud / Gemini Enterprise), we can **fully automate**: push the digest as a source and trigger the audio overview from the command line. No copy-paste, no manual steps.

### What we need from you

| Item | Where to get it | Example |
|------|-----------------|--------|
| **Project number** | Google Cloud Console → your project → Dashboard (numeric ID) | `123456789012` |
| **Location** | Region for the API: `global`, `us`, or `eu` | `global` |
| **Notebook ID** | Either create one via API once and reuse, or from the notebook URL: `.../notebook/NOTEBOOK_ID?project=...` | `abc123def456` |
| **Authentication** | One of: (1) **gcloud** — run `gcloud auth application-default login` (or `gcloud auth login --enable-gdrive-access` if using Docs); (2) **Service account** — JSON key file path for a service account with NotebookLM API access | — |

### Setup steps (one-time)

1. **NotebookLM Enterprise**  
   - Your org must have [NotebookLM Enterprise set up](https://cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/set-up-notebooklm) and you must have access.

2. **Create a notebook (if you don’t have one)**  
   - We can do this via API once and store the notebook ID, or you create one in the UI at  
     `https://notebooklm.cloud.google.com/LOCATION/?project=PROJECT_NUMBER`  
   - From the notebook URL, copy the **NOTEBOOK_ID**.

3. **Auth**  
   - **Option 1 (user account):**  
     `gcloud auth application-default login`  
     (and, if you add Google Docs as sources later: `gcloud auth login --enable-gdrive-access`)  
   - **Option 2 (service account):**  
     Create a key in Cloud Console, download JSON, set env var:  
     `GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\key.json`

4. **Environment variables** (e.g. in `research_agent\.env`):

   ```env
   NOTEBOOKLM_PROJECT_NUMBER=123456789012
   NOTEBOOKLM_LOCATION=global
   NOTEBOOKLM_NOTEBOOK_ID=your_notebook_id_here
   ```

With that, a script can:

- Run the research scan and build the digest.
- Call the NotebookLM Enterprise API to add (or replace) the digest as a **text source** (no Google Doc needed).
- Call the API to **create an audio overview** (~20 min style when the API supports it).

If you have Enterprise and can share the **project number**, **location**, and **notebook ID** (and confirm you’ve done the auth step), we can wire the script to use them. **Do not put service account JSON contents or long-lived tokens in chat** — use env vars or local files and keep them out of git.

---

## Option B: Public NotebookLM (notebooklm.google.com) — no official API

The **free/public** NotebookLM at [notebooklm.google.com](https://notebooklm.google.com) has **no official API**. Google does not provide a way to add sources or generate audio programmatically for this version.

So we **cannot** “plug into your NotebookLM” in an automated way without one of these workarounds:

### What we can do

1. **Keep the current flow (manual)**  
   - Export: `python scanner.py --export-notebooklm digest_for_notebooklm.md`  
   - You paste the file into a Google Doc and add that Doc as a source in NotebookLM, then click “Generate audio overview” and choose “Longer” (~20 min).  
   - No credentials needed; the only “thing we need” from your NotebookLM is: **you** doing the paste and one click.

2. **Half-automate with Google Docs API**  
   - We could automate only the “update the Doc” part: a script creates or updates a **specific Google Doc** with the latest digest.  
   - **What we’d need from you:**  
     - A **Google Cloud project** (any project, no need for NotebookLM Enterprise).  
     - **OAuth 2.0 client** (Desktop app) and one-time sign-in so we can write to that Doc.  
     - The **Document ID** of the Doc you always use for this (from the URL: `docs.google.com/document/d/DOCUMENT_ID/edit`).  
   - Then **you** would still: open NotebookLM, add that Doc as a source (or leave it added), and click “Generate audio overview.” So the only thing we’d automate is “refresh the Doc with the latest digest.”

3. **Browser automation (unofficial)**  
   - Some people use tools like [notebooklm-podcast-automator](https://github.com/israelbls/notebooklm-podcast-automator) (Playwright) to drive the public NotebookLM UI.  
   - That would require you to run that tool yourself and log in in the automated browser; we don’t get “something from your NotebookLM” — we’d be automating the browser instead.  
   - We could point you to that repo and outline how to run it with our export, but we wouldn’t hold any credentials or “connect” to your NotebookLM account from our script.

---

## Summary

| You have | What we need from “your NotebookLM” to automate |
|----------|--------------------------------------------------|
| **NotebookLM Enterprise** | Project number, location, notebook ID, and auth (gcloud or service account). We can then push the digest and trigger the podcast via API. |
| **Public NotebookLM only** | No API to “plug into.” We can either: (1) keep export + you paste and click once, or (2) add Docs API so we update one Doc and you still click “Generate” in the UI, or (3) point you to browser-automation tools. |

If you tell me which you have (Enterprise vs public) and, for Enterprise, that you’re okay sharing project number + location + notebook ID (and that auth is set up), I can outline or add the exact script steps for your case.
