"""Tests for the filtering logic in main.py - the code that caused the outage."""

import time

import pytest

from main import (filter_software_jobs, has_software_context, is_qa_role,
                  is_recent)

HOUR = 3600
NOW = 1_757_000_000.0


def job(**overrides):
    base = {
        "job_id": "abc",
        "job_title": "QA Engineer",
        "job_description": "Software automation testing role, agile team",
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


# --- is_qa_role ------------------------------------------------------------

@pytest.mark.parametrize("title", [
    "QA Engineer",
    "Senior SDET",
    "Test Automation Engineer",
    "Software Quality Assurance Analyst",
    "Tester (1 Year Contract)",
    "Test Lead",
])
def test_is_qa_role_accepts_qa_titles(title):
    assert is_qa_role(job(job_title=title)) is True


@pytest.mark.parametrize("title", [
    # Real titles the loose filter let through into the production group.
    "Site Reliability Engineer - Elite Quant Fund",
    "Network Engineer Team Lead",
    "Defectivity Control Engineer",
    "Lead - VM & App Security Engineer",
    "System Engineer(HPC)",
    "Manager, Assurance & Advisory",
    "Lead Engineering Manager, Engagement And Case Study Management Programme",
])
def test_is_qa_role_rejects_non_qa_titles(title):
    assert is_qa_role(job(job_title=title)) is False


@pytest.mark.parametrize("title", [
    # Say "test" but are not software: engine test cells, hardware field test.
    "Field Test Engineer",
    "Technician/ Lead Technician (Test Cell)",
    "Assistant Manager - Mechanical Engineering",
    "Calibration Test Engineer",
])
def test_is_qa_role_rejects_non_software_test_domains(title):
    assert is_qa_role(job(job_title=title)) is False


def test_is_qa_role_is_case_insensitive():
    assert is_qa_role(job(job_title="senior qa automation engineer")) is True


def test_is_qa_role_survives_none_title():
    assert is_qa_role({"job_title": None}) is False


def test_is_qa_role_does_not_read_description():
    """The signal must be in the title; descriptions mention QA constantly."""
    assert is_qa_role(job(job_title="Data Engineer",
                          job_description="work with our QA test team")) is False


# --- has_software_context --------------------------------------------------

def test_software_context_from_description():
    assert has_software_context(job(job_title="QA Engineer",
                                    job_description="Selenium and CI/CD")) is True


def test_software_context_rejects_office_applications():
    """Regression: a bare "application" matched "microsoft office applications"
    in a manufacturing QA listing and let it through."""
    j = job(job_title="Engineer, Customer Quality Assurance",
            job_description="proficiency in microsoft office applications. "
                            "failure analysis of products")
    assert has_software_context(j) is False


def test_software_context_rejects_industrial_automation():
    j = job(job_title="Automation Engineer BMS/EMS",
            job_description="building management and energy management systems")
    assert has_software_context(j) is False


def test_software_context_survives_none_fields():
    assert has_software_context({"job_title": None, "job_description": None}) is False


# --- filter_software_jobs --------------------------------------------------

def test_filter_requires_qa_title_software_context_and_recency():
    jobs = [
        job(job_id="keep", job_title="QA Automation Engineer",
            job_description="Selenium, CI/CD", job_posted_at_timestamp=NOW - 10 * HOUR),
        job(job_id="stale", job_title="QA Automation Engineer",
            job_description="Selenium, CI/CD", job_posted_at_timestamp=NOW - 200 * HOUR),
        job(job_id="not-qa", job_title="Network Engineer Team Lead",
            job_description="Selenium, CI/CD", job_posted_at_timestamp=NOW - 10 * HOUR),
        job(job_id="not-software", job_title="Quality Assurance Engineer",
            job_description="failure analysis of moulded products",
            job_posted_at_timestamp=NOW - 10 * HOUR),
    ]
    kept = filter_software_jobs(jobs, now=NOW)
    assert [j["job_id"] for j in kept] == ["keep"]


def test_filter_empty_input():
    assert filter_software_jobs([], now=NOW) == []
