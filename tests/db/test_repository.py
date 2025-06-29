# tests/test_job_repository.py

import os
import sqlite3
import pytest
from db.repository import JobRepository

TEST_DB_FILE = "test_jobs.db"

@pytest.fixture
def job_repo():
    # Setup: create a fresh test DB
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
    repo = JobRepository(TEST_DB_FILE)
    yield repo
    # Teardown
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

def test_insert_and_fetch_unsent_jobs(job_repo):
    sample_jobs = [
        {
            "job_id": "job123",
            "job_title": "QA Engineer",
            "employer_name": "Test Company",
            "job_location": "Singapore",
            "job_apply_link": "https://apply.test.com",
            "apply_options": [],
            "job_posted_at": "2025-06-29"
        }
    ]

    job_repo.insert_jobs(sample_jobs)
    jobs = job_repo.fetch_unsent_jobs(10)

    assert len(jobs) == 1
    assert jobs[0][0] == "job123"  # job_id
    assert jobs[0][1] == "QA Engineer"
    assert jobs[0][2] == "Test Company"

def test_insert_duplicate_job(job_repo):
    job = {
        "job_id": "dup-job",
        "job_title": "QA Lead",
        "employer_name": "Dup Corp",
        "job_location": "SG",
        "job_apply_link": "https://dup.com/apply",
        "apply_options": [],
        "job_posted_at": "2025-06-29"
    }
    job_repo.insert_jobs([job])
    job_repo.insert_jobs([job])  # Try to insert again

    jobs = job_repo.fetch_unsent_jobs(10)
    assert len(jobs) == 1  # No duplicate

def test_mark_as_sent(job_repo):
    job = {
        "job_id": "send-job",
        "job_title": "Send Me",
        "employer_name": "Senders Inc",
        "job_location": "SG",
        "job_apply_link": "https://senders.com",
        "apply_options": [],
        "job_posted_at": "2025-06-29"
    }
    job_repo.insert_jobs([job])
    job_repo.mark_as_sent("send-job")

    jobs = job_repo.fetch_unsent_jobs(10)
    assert len(jobs) == 0  # Should not return sent jobs

def test_delete_all_jobs(job_repo):
    job = {
        "job_id": "del-job",
        "job_title": "Delete Me",
        "employer_name": "Gone Co",
        "job_location": "SG",
        "job_apply_link": "https://gone.com",
        "apply_options": [],
        "job_posted_at": "2025-06-29"
    }
    job_repo.insert_jobs([job])
    job_repo.delete_all_jobs()

    conn = sqlite3.connect(TEST_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM jobs")
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 0
