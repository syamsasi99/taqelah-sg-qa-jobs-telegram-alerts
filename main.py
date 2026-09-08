"""Fetch QA job listings from JSearch and send unseen ones to Telegram."""

import os
import sys
import time

from dotenv import load_dotenv

from builder.job_messsage import JobMessageBuilder
from db.repository import JobRepository
from jsearch.job_fetcher import JobFetcher
from notifier.telegram import TelegramNotifier
from utils.logger import get_logger

logger = get_logger(__name__)

# Load .env for local runs. Real environment variables (e.g. CI secrets)
# always win - load_dotenv does not override what is already set.
load_dotenv()

DB_FILE = os.getenv("DB_FILE", "jobs.db")
MAX_JOBS = int(os.getenv("MAX_JOBS", "30"))
SEND_DELAY_SECONDS = float(os.getenv("SEND_DELAY_SECONDS", "1"))

# JSearch's index lags real posting time by roughly 29-46 hours, so nothing it
# returns is ever under 24h old - which is why matching "hours"/"minutes" in
# job_posted_at silently dropped every job. 48h is the window that actually
# matches what the API serves; JobRepository stops the resulting overlap
# between consecutive daily runs from producing duplicate messages.
RECENT_WINDOW_HOURS = float(os.getenv("RECENT_WINDOW_HOURS", "48"))

QUERIES = (
    "test qa engineer jobs in singapore",
    "lead qa test engineer jobs in singapore",
    "principal qa test engineer jobs in singapore",
    "manager qa test engineer jobs in singapore",
)

KEYWORDS = (
    "software", "manual", "automation", "selenium",
    "cypress", "playwright", "appium", "web", "mobile",
)


def matches_keywords(job):
    """True if the job title or description mentions a tracked keyword."""
    haystack = f"{job.get('job_title') or ''} {job.get('job_description') or ''}"
    return any(keyword in haystack.lower() for keyword in KEYWORDS)


def is_recent(job, now=None, window_hours=None):
    """True if job_posted_at_timestamp falls inside the recency window.

    Uses the epoch timestamp rather than the human-readable job_posted_at
    string, which changes wording ("1 day ago", "Today", "Just posted") and
    cannot be matched reliably.
    """
    timestamp = job.get("job_posted_at_timestamp")
    if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)):
        return False

    window = RECENT_WINDOW_HOURS if window_hours is None else window_hours
    age_hours = ((time.time() if now is None else now) - timestamp) / 3600
    # Tolerate an hour of clock skew putting a fresh job slightly in the future.
    return -1 <= age_hours <= window


def filter_software_jobs(jobs, now=None):
    """Keep recent, QA-relevant jobs and log how many survive each stage."""
    by_keyword = [job for job in jobs if matches_keywords(job)]
    recent = [job for job in by_keyword if is_recent(job, now=now)]
    logger.info(
        "Filter funnel: fetched %d -> keyword %d -> recent (<=%gh) %d",
        len(jobs), len(by_keyword), RECENT_WINDOW_HOURS, len(recent),
    )
    return recent


def main():
    """Main entry point. Returns a process exit code."""
    logger.info("Starting....")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not bot_token or not chat_id:
        logger.error("❌ BOT_TOKEN or CHAT_ID is missing.")
        return 1

    fetcher = JobFetcher(
        api_host="jsearch.p.rapidapi.com",
        api_key=os.getenv("RAPIDAPI_KEY"),
    )

    jobs = []
    for query in QUERIES:
        jobs += fetcher.fetch(query=query, num_pages=1)

    if fetcher.error_count == len(QUERIES):
        logger.error(
            "❌ All %d queries failed - this is an outage, not a quiet day.",
            len(QUERIES),
        )
        return 1

    jobs = filter_software_jobs(jobs)
    unique_jobs = {job["job_id"]: job for job in jobs if job.get("job_id")}

    repo = JobRepository(DB_FILE)
    repo.insert_jobs(list(unique_jobs.values()))
    unsent_ids = {row[0] for row in repo.fetch_unsent_jobs(MAX_JOBS)}
    to_send = [job for job_id, job in unique_jobs.items() if job_id in unsent_ids]

    logger.info(
        "Unique %d -> already sent %d -> sending %d",
        len(unique_jobs), len(unique_jobs) - len(to_send), len(to_send),
    )

    if not to_send:
        logger.info("📭 No new QA jobs found.")
        return 0

    notifier = TelegramNotifier(bot_token, chat_id)
    failures = 0

    for index, job in enumerate(to_send, start=1):
        message = JobMessageBuilder.build(job)
        logger.info("Sending job %d/%d...", index, len(to_send))
        if notifier.send(message):
            repo.mark_as_sent(job["job_id"])
        else:
            failures += 1
        if index < len(to_send):
            time.sleep(SEND_DELAY_SECONDS)

    if failures:
        logger.error("❌ %d of %d messages failed to send.", failures, len(to_send))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
