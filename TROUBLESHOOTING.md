# Daily drops stopped — troubleshooting

If your daily microlearning notes are no longer appearing in Obsidian, check the following in order.

---

## 1. Is the workflow running?

- Open the **GitHub repo** that Obsidian syncs from (e.g. **StarryDynamo/my-learning**).
- Go to **Actions** → **Daily Microlearning**.
- Check the **last run**: did it run today or yesterday? Did it **succeed** (green) or **fail** (red)?

If there are **no runs** or the workflow is missing:
- The repo you're looking at might not be the one that has the workflow. The workflow lives in **`.github/workflows/daily-microlearning.yml`** at the **root** of the repo (same level as `generate.py`).
- If you use a different repo (e.g. only **my-coaches** with midnight-intel), that repo doesn't have this workflow unless you added the microlearning-agent folder and its `.github` at the root. **Fix:** Either use the repo that contains `generate.py` and `.github/workflows/daily-microlearning.yml`, or add that workflow to the repo you sync with Obsidian.

If the run **failed**, open the failed run and check the **logs** (see below).

---

## 2. API key (most common cause of failures)

The workflow needs **one** of these repo secrets (Settings → Secrets and variables → Actions):

- **OPENAI_API_KEY** (if you use OpenAI in `config.json`), or  
- **ANTHROPIC_API_KEY** (if you use Anthropic).

If you **rotated or recreated** your API key and didn't update the repo secret, the "Generate microlearning" step will fail.

**Fix:** Update the secret with the current key and re-run the workflow (Actions → Daily Microlearning → Run workflow).

---

## 3. Generate step failing (logs)

In the failed run, open the **"Generate microlearning"** step. Look for:

- **401 / 403** → invalid or expired API key (update the secret).
- **ModuleNotFoundError** → dependency issue (workflow uses `pip install -r requirements.txt`; ensure `requirements.txt` is at repo root).
- **File not found** (e.g. `config.json`) → repo layout is wrong; `generate.py` and `config.json` must be at the **root** of the checked-out repo.

---

## 4. Commit step failing

If "Commit and push" fails:

- **Nothing to commit** → the workflow might think no files changed. Check that `generate.py` actually writes to `Microlearning/<Topic>/...` and updates `learning-tracker.json` (see `config.json` → `output_dir`).
- **Permission denied** → the job needs `contents: write`. The workflow already has `permissions: contents: write`; don't remove it.

---

## 5. Commits on GitHub but not pulling into Obsidian (auto-pull 10 min)

If you **see the drops in GitHub** (new commits with microlearning notes) but they **don't appear in Obsidian** even with pull interval set (e.g. 10 minutes):

### A. Which folder is Obsidian Git syncing?

- **Obsidian** → Settings → Community plugins → **Obsidian Git** → check **"Git repository path"** (or equivalent). It must point at the **same folder** that is a clone of the repo where the workflow pushes (e.g. **my-learning**).
- If your **vault** is "Tom's Vault" and the microlearning repo is a **subfolder** (e.g. `Tom's Vault/my-learning/`), then Obsidian Git must be set to use **that subfolder** as the repository path, not the vault root. Otherwise it will pull a different repo (or none) and you won't see the new files.
- **Fix:** Set the repository path to the folder that contains `.git` for the my-learning (microlearning) repo.

### B. Pull manually and watch for errors

- In Obsidian: open the **Command palette** (Ctrl/Cmd+P) → run **"Obsidian Git: Pull"** (or use the plugin's Pull button if it has one).
- Check the **notice** at the top or bottom of the window for any error (e.g. "Pull failed", "Authentication failed", "Merge conflict").
- If you see an error, note it and fix (see C–E below).

### C. Confirm from the shell that the folder is the right repo and can pull

1. In File Explorer / Finder, go to the folder that **should** contain the microlearning repo (e.g. `Tom's Vault/my-learning` or your vault root if the whole vault is that repo).
2. Open a terminal in that folder and run:
   ```bash
   git status
   git remote -v
   git pull
   ```
3. **If `git pull` fails:** the message (auth, conflict, etc.) is the cause. Fix auth (token/SSH) or resolve conflicts, then try Pull again in Obsidian.
4. **If `git pull` succeeds** and new files appear in that folder but **not** in Obsidian: Obsidian might be showing a different folder (e.g. vault path or Git path is wrong). Point Obsidian's vault or Obsidian Git at the folder where you just ran `git pull`.

### D. Auto-pull not running

- Some setups only run auto-pull when the vault has been **in focus** for a bit. Try leaving Obsidian open and focused for 10+ minutes and see if the note appears.
- **Backup interval** in Obsidian Git can conflict or delay; try temporarily setting pull interval to **1** minute to test, then set it back.
- On **mobile**, auto-pull often runs only when you open the vault; do a manual **Pull** after opening.

### E. Merge conflicts or dirty working tree

- If you (or another device) edited the same files in the repo, Git might have **merge conflicts** or a dirty state and refuse to pull.
- In the repo folder run: `git status`. If it says "You have uncommitted changes" or "merge conflict", resolve them (e.g. commit or stash local changes, then pull), or use "Obsidian Git: Pull" after resolving in a terminal.

---

## 6. Schedule (cron) not running

GitHub can **disable** scheduled workflows if the repo has no activity for a long time. Check:

- **Actions** tab → **Daily Microlearning** → any runs in the last week?
- If there are no scheduled runs at all, trigger once manually (Run workflow). If that works, the schedule may have been paused; re-enable or use **workflow_dispatch** from your phone (GitHub Mobile → Actions → Run workflow) as a workaround.

---

## 7. Quick checklist

| Check | Where |
|-------|--------|
| Workflow exists and runs | Repo → Actions → Daily Microlearning |
| API key set and valid | Repo → Settings → Secrets and variables → Actions |
| Generate step logs | Click a run → "Generate microlearning" step |
| Commit step runs after generate | Same run → "Commit and push" step |
| Obsidian syncs from this repo | Obsidian Git → which repo? Same as above? |
| Pull interval or manual pull | Obsidian Git settings / Pull button |

---

## 8. Manual run (to test end-to-end)

1. **From GitHub:** Actions → Daily Microlearning → **Run workflow** → Run workflow.
2. Wait for the run to finish (green).
3. In Obsidian: **Pull** (or wait for auto-pull).
4. Check **Microlearning/** (or your `output_dir`) for today's note.

If the manual run succeeds but you still don't see the note in Obsidian, the issue is the **Obsidian Git** target or path, not the workflow.
