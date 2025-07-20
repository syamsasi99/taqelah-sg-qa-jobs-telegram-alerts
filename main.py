"""Main script for loading mock jobs and sending them via Telegram."""

import json
import os

from builder.job_messsage import JobMessageBuilder
from db.repository import JobRepository
from jsearch.job_fetcher import JobFetcher
from notifier.telegram import TelegramNotifier
from utils.logger import get_logger

logger = get_logger(__name__)

MOCK_DATA_FILE = "data/mock_data.json"
DB_FILE = "jobs.db"
MAX_JOBS = 30


def load_mock_jobs():
    """
    Load mock job data from a JSON file.

    Returns:
        list: List of mock job entries.
    """
    logger.info("Loading the mock data..")
    with open(MOCK_DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)
        return data.get("data", [])


def filter_software_jobs(jobs):
    """
    Filters job listings based on keywords in description and posting time.

    Includes jobs posted within the last 24 hours (e.g., '1 day ago', 'hours ago', 'minutes ago')
    and with relevant keywords: 'software', 'manual', or 'automation'.
    """
    keywords = ("software", "manual", "automation", "selenium", "cypress", "playwright", "appium", "web", "mobile")
    recent_indicators = ("hours", "minutes")

    return [
        job for job in jobs
        if any(keyword in str(job.get("job_description", "")).lower() for keyword in keywords)
           and any(indicator in str(job.get("job_posted_at", "")).lower() for indicator in recent_indicators)
    ]


def main():
    """Main entry point of the script."""

    logger.info("Starting....")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not bot_token or not chat_id:
        logger.error("❌ BOT_TOKEN or CHAT_ID is missing.")
        return

    # jobs = load_mock_jobs()

    fetcher = JobFetcher(
        api_host="jsearch.p.rapidapi.com",
        api_key=os.getenv("RAPIDAPI_KEY")
    )

    qa_test_engineer_jobs = fetcher.fetch(query="test qa engineer jobs in singapore", num_pages=1)
    lead_qa_engineer_jobs = fetcher.fetch(query="lead qa test engineer jobs in singapore", num_pages=1)
    principal_qa_engineer_jobs = fetcher.fetch(query="principal qa test engineer jobs in singapore", num_pages=1)
    manager_qa_engineer_jobs = fetcher.fetch(query="manager qa test engineer jobs in singapore", num_pages=1)
    jobs = qa_test_engineer_jobs + lead_qa_engineer_jobs + manager_qa_engineer_jobs + principal_qa_engineer_jobs
    jobs = filter_software_jobs(jobs)
    unique_jobs = {job['job_id']: job for job in jobs}
    jobs = list(unique_jobs.values())

    notifier = TelegramNotifier(bot_token, chat_id)

    if not jobs:
        logger.info("📭 No new QA jobs found.")
        return

    for index, job in enumerate(jobs, start=1):
        message = JobMessageBuilder.build(job)
        logger.info("Sending job %d/%d...", index, len(jobs))
        notifier.send(message)


if __name__ == "__main__":
    main()
