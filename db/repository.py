"""Job repository for interacting with the jobs SQLite database."""

import sqlite3
from typing import List, Tuple, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class JobRepository:
    """Handles database operations for job records."""

    def __init__(self, db_file: str):
        """Initialize JobRepository and create table if it doesn't exist."""
        self.db_file = db_file
        self._init_db()

    def _init_db(self) -> None:
        """Initializes the SQLite database and creates the jobs table."""
        logger.info("Initializing database...")
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    apply_link TEXT,
                    posted_at TEXT,
                    is_sent INTEGER DEFAULT 0
                )
            """)

    def fetch_unsent_jobs(self, limit: int) -> List[Tuple]:
        """Fetch jobs that have not been sent yet."""
        logger.info("Fetching unsent jobs...")
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            return cursor.execute("""
                SELECT job_id, title, company, location, apply_link, posted_at
                FROM jobs
                WHERE is_sent = 0
                ORDER BY posted_at DESC
                LIMIT ?
            """, (limit,)).fetchall()

    def mark_as_sent(self, job_id: str) -> None:
        """Mark a job as sent based on its job_id."""
        logger.info("Marking job as sent: %s", job_id)
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("UPDATE jobs SET is_sent = 1 WHERE job_id = ?", (job_id,))
            conn.commit()

    def insert_jobs(self, jobs: List[dict]) -> None:
        """Insert new job entries into the database."""
        logger.info("Inserting new jobs...")
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            count = 0
            for job in jobs:
                links = [job.get("job_apply_link", "")]
                for option in job.get("apply_options", []):
                    link = option.get("apply_link")
                    if link and link not in links:
                        links.append(link)
                all_links = ",".join(links)
                try:
                    cursor.execute("""
                        INSERT INTO jobs (job_id, title, company, location, apply_link, posted_at, is_sent)
                        VALUES (?, ?, ?, ?, ?, ?, 0)
                    """, (
                        job["job_id"],
                        job["job_title"],
                        job["employer_name"],
                        job.get("job_location", "Singapore"),
                        all_links,
                        job.get("job_posted_at", "")
                    ))
                    count += 1
                except sqlite3.IntegrityError:
                    logger.warning("Job already exists in database: %s", job["job_id"])
                    continue
            conn.commit()
        logger.info("Inserted %d new jobs.", count)

    def delete_all_jobs(self) -> None:
        """Delete all job records from the database."""
        logger.warning("Deleting all job records...")
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("DELETE FROM jobs")
            conn.commit()
        logger.info("All job records have been deleted.")
