"""Tests for the filtering logic in main.py - the code that caused the outage."""

import time

import pytest

from main import filter_software_jobs, is_recent, matches_keywords

HOUR = 3600
NOW = 1_757_000_000.0


def job(**overrides):
    base = {
        "job_id": "abc",
        "job_title": "QA Engineer",
        "job_description": "Automation testing role",
        "job_posted_at_timestamp": NOW - 5 * HOUR,
    }
    base.update(overrides)
    return base


# --- is_recent -------------------------------------------------------------

@pytest.mark.parametrize("age_hours,expected", [
    (0, True),
    (5, True),
    (29.2, True),    # freshest thing JSearch actually serves
    (47.9, True),
    (48.1, False),
    (102, False),
])
def test_is_recent_window(age_hours, expected):
    j = job(job_posted_at_timestamp=NOW - age_hours * HOUR)
    assert is_recent(j, now=NOW, window_hours=48) is expected


def test_is_recent_regression_one_day_ago():
    """The exact shape that broke prod: '1 day ago', ~29h old, must pass.

    The old filter looked for 'hours'/'minutes' in job_posted_at and dropped
    100% of jobs because JSearch's index lag means nothing is ever <24h old.
    """
    j = job(job_posted_at="1 day ago",
            job_posted_at_timestamp=NOW - 29.2 * HOUR)
    assert is_recent(j, now=NOW, window_hours=48) is True


def test_is_recent_tolerates_small_clock_skew():
    assert is_recent(job(job_posted_at_timestamp=NOW + 0.5 * HOUR),
                     now=NOW, window_hours=48) is True


def test_is_recent_rejects_far_future():
    assert is_recent(job(job_posted_at_timestamp=NOW + 10 * HOUR),
                     now=NOW, window_hours=48) is False


@pytest.mark.parametrize("bad", [None, "", "1 day ago", True, {}])
def test_is_recent_rejects_non_numeric_timestamp(bad):
    assert is_recent(job(job_posted_at_timestamp=bad), now=NOW) is False


def test_is_recent_rejects_missing_timestamp():
    j = job()
    del j["job_posted_at_timestamp"]
    assert is_recent(j, now=NOW) is False


def test_is_recent_defaults_to_wall_clock():
    assert is_recent(job(job_posted_at_timestamp=time.time() - HOUR)) is True


# --- matches_keywords ------------------------------------------------------

def test_matches_keyword_in_description():
    assert matches_keywords(job(job_title="Engineer",
                                job_description="Selenium suite")) is True


def test_matches_keyword_in_title_only():
    """Regression: the old filter only searched job_description."""
    assert matches_keywords(job(job_title="Mobile Test Engineer",
                                job_description="")) is True


def test_matches_keyword_is_case_insensitive():
    assert matches_keywords(job(job_title="", job_description="AUTOMATION")) is True


def test_no_keyword_match():
    assert matches_keywords(job(job_title="Chef",
                                job_description="Cooking role")) is False


def test_matches_keywords_survives_none_fields():
    assert matches_keywords({"job_title": None, "job_description": None}) is False


# --- filter_software_jobs --------------------------------------------------

def test_filter_requires_both_keyword_and_recency():
    jobs = [
        job(job_id="keep", job_posted_at_timestamp=NOW - 10 * HOUR),
        job(job_id="stale", job_posted_at_timestamp=NOW - 200 * HOUR),
        job(job_id="offtopic", job_title="Chef", job_description="Cooking",
            job_posted_at_timestamp=NOW - 10 * HOUR),
    ]
    kept = filter_software_jobs(jobs, now=NOW)
    assert [j["job_id"] for j in kept] == ["keep"]


def test_filter_empty_input():
    assert filter_software_jobs([], now=NOW) == []
