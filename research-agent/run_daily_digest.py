#!/usr/bin/env python3
"""
Run the research agent daily at 8:00 AM Melbourne time and write to Obsidian vault.
Leave this script running (e.g. in a terminal or as a scheduled task that starts at logon).
"""
from __future__ import annotations

import logging
import pathlib
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from vault_article import run_and_write_vault

MELBOURNE_TZ = ZoneInfo("Australia/Melbourne")

LOG_FILE = pathlib.Path(__file__).resolve().parent / "daily_digest.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


def job() -> None:
    log.info("Running daily research digest → Obsidian vault...")
    try:
        filepath, count = run_and_write_vault(window_days=7, include_papers=True)
        log.info("Wrote %s (%d items)", filepath, count)
    except Exception as e:
        log.error("Vault write failed: %s", e)


if __name__ == "__main__":
    load_dotenv(pathlib.Path(__file__).resolve().parent / ".env")

    log.info("Research Agent daily scheduler: 8:00 AM Melbourne → Obsidian vault. Ctrl+C to stop.")

    last_run_date: str | None = None
    while True:
        try:
            now = datetime.now(MELBOURNE_TZ)
            today = now.strftime("%Y-%m-%d")
            if now.hour == 8 and last_run_date != today:
                job()
                last_run_date = today
        except Exception as e:
            log.exception("Job failed: %s", e)
        time.sleep(60)
