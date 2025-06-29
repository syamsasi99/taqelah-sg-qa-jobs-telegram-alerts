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
    filtered_jobs = []
    for job in jobs:
        description = job.get("job_description", "").lower()
        if "software" in description or "manual" in description or "automation" in description:
            filtered_jobs.append(job)
    return filtered_jobs


def main():
    """Main entry point of the script."""



    logger.info("Starting....")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not bot_token or not chat_id:
        logger.error("❌ BOT_TOKEN or CHAT_ID is missing.")
        return

    repo = JobRepository(DB_FILE)
    # jobs = load_mock_jobs()

    all_jobs = repo.fetch_all_jobs()
    for job in all_jobs:
        print(job)

    fetcher = JobFetcher(
        api_host="jsearch.p.rapidapi.com",
        api_key=os.getenv("RAPIDAPI_KEY")
    )

    qa_test_engineer_jobs = fetcher.fetch(query="test qa engineer jobs in singapore", num_pages=1)
    lead_qa_engineer_jobs = fetcher.fetch(query="lead qa test engineer jobs in singapore", num_pages=1)
    manager_qa_engineer_jobs = fetcher.fetch(query="manager qa test engineer jobs in singapore", num_pages=1)
    jobs = qa_test_engineer_jobs + lead_qa_engineer_jobs + manager_qa_engineer_jobs
    jobs = filter_software_jobs(jobs)
    unique_jobs = {job['job_id']: job for job in jobs}
    jobs = list(unique_jobs.values())
    repo.insert_jobs(jobs)

    notifier = TelegramNotifier(bot_token, chat_id)
    jobs = repo.fetch_unsent_jobs(limit=MAX_JOBS)

    if not jobs:
        logger.info("📭 No new QA jobs found.")
        return

    for index, job in enumerate(jobs, start=1):
        message = JobMessageBuilder.build(job)
        logger.info("Sending job %d/%d...", index, len(jobs))
        if notifier.send(message):
            repo.mark_as_sent(job[0])

    all_jobs = repo.fetch_all_jobs()
    for job in all_jobs:
        print(job)


if __name__ == "__main__":
    main()
