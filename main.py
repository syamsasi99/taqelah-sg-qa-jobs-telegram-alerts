"""Fetch QA job listings from JSearch and send unseen ones to Telegram."""

import os
import re
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

# A QA/test signal must appear in the TITLE. Searching the description for
# generic words like "software" or "web" matched nearly every tech listing and
# let through SREs, network engineers and mechanical engineers.
TITLE_SIGNALS = (
    r"\bqa\b", r"\bq\.a\.", r"quality assurance", r"quality engineer",
    r"\bsdet\b", r"tester", r"test engineer", r"test automation",
    r"automation engineer", r"test analyst", r"test lead", r"test manager",
    r"testing", r"\bsoftware quality\b",
)

# Non-software disciplines that still say "test" or "quality" in the title:
# engine test cells, semiconductor defectivity, calibration labs.
TITLE_DENY = (
    r"field test", r"test cell", r"mechanical", r"electrical", r"civil",
    r"chemical", r"semiconductor", r"defectivity", r"wafer", r"laborator",
    r"calibration", r"non-destructive", r"technician", r"welding",
)

# Evidence the role is about software rather than manufacturing or facilities.
SOFTWARE_CONTEXT = (
    # NB: no bare "application" - it matches "microsoft office applications"
    # in manufacturing QA listings.
    r"\bsoftware\b", r"\bsdlc\b", r"\bagile\b", r"\bscrum\b",
    r"\bapi\b", r"selenium", r"cypress", r"playwright", r"appium", r"postman",
    r"automation framework", r"test case", r"test script", r"regression test",
    r"ci/cd", r"jenkins", r"devops", r"\bjira\b", r"back-?end", r"front-?end",
    r"web app", r"mobile app", r"microservice",
)


def _matches(patterns, text):
    lowered = (text or "").lower()
    return any(re.search(pattern, lowered) for pattern in patterns)


def is_qa_role(job):
    """True if the job TITLE names a QA/test role in a software discipline."""
    title = job.get("job_title") or ""
    if _matches(TITLE_DENY, title):
        return False
    return _matches(TITLE_SIGNALS, title)


def has_software_context(job):
    """True if the title or description shows this is a software role.

    Guards against industrial and manufacturing QA - "Automation Engineer
    BMS/EMS", "Senior Quality Assurance Manager" at a factory - which clear
    the title check but are not what this bot is for.
    """
    return _matches(SOFTWARE_CONTEXT,
                    f"{job.get('job_title') or ''} {job.get('job_description') or ''}")


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
    """Keep recent, software-QA jobs and log how many survive each stage."""
    qa_roles = [job for job in jobs if is_qa_role(job)]
    software = [job for job in qa_roles if has_software_context(job)]
    recent = [job for job in software if is_recent(job, now=now)]
    logger.info(
        "Filter funnel: fetched %d -> qa title %d -> software %d -> recent (<=%gh) %d",
        len(jobs), len(qa_roles), len(software), RECENT_WINDOW_HOURS, len(recent),
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
