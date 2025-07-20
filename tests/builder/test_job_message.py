from builder.job_messsage import JobMessageBuilder


def test_get_source_with_valid_url():
    url = "https://www.linkedin.com/jobs/view/123"
    assert JobMessageBuilder.get_source(url) == "linkedin.com"


def test_get_source_without_www():
    url = "https://angel.co/jobs/view/456"
    assert JobMessageBuilder.get_source(url) == "angel.co"


def test_get_source_invalid_url():
    url = "not-a-url"
    assert JobMessageBuilder.get_source(url) == "apply"


def test_build_full_details():
    job = {
        "job_title": "QA Engineer",
        "employer_name": "Rakuten",
        "job_is_remote": False,
        "job_location": "Singapore",
        "job_country": "SG",
        "job_description": "Hybrid work setup available",
        "job_employment_type": "full time",
        "job_min_salary": 4000,
        "job_max_salary": 7000,
        "job_salary_period": "month",
        "job_apply_link": "https://jobs.rakuten.com/apply/qa",
        "apply_options": [
            {"apply_link": "https://linkedin.com/apply/rakuten-qa"}
        ],
        "job_posted_at": "2025-07-20"
    }

    message = JobMessageBuilder.build(job)

    assert "📋 <b>QA Engineer</b>" in message
    assert "🏢 <i>Rakuten</i>" in message
    assert "🌍 Location: Singapore" in message
    assert "🏠 Arrangement: Hybrid" in message
    assert "📌 Status: Full Time" in message
    assert "💰 Salary: $4,000 – $7,000 per Month" in message
    assert "🔗 <a href='https://jobs.rakuten.com/apply/qa'>jobs.rakuten.com</a>" in message
    assert "🔗 <a href='https://linkedin.com/apply/rakuten-qa'>linkedin.com</a>" in message


def test_build_remote_min_salary_only():
    job = {
        "job_title": "Backend Developer",
        "employer_name": "GitHub",
        "job_is_remote": True,
        "job_min_salary": 100000,
        "job_salary_period": "year",
        "job_posted_at": "2025-07-20",
        "job_description": "",
        "job_employment_type": "contract",
        "job_apply_link": "https://github.com/jobs/123"
    }

    message = JobMessageBuilder.build(job)

    assert "🌍 Location: Worldwide" in message
    assert "🏠 Arrangement: Remote" in message
    assert "📌 Status: Contract" in message
    assert "💰 Salary: From $100,000" in message


def test_build_no_salary_no_links():
    job = {
        "job_title": "UX Designer",
        "employer_name": "Adobe",
        "job_is_remote": False,
        "job_country": "US",
        "job_description": "Office-based work",
        "job_employment_type": "part time",
        "job_posted_at": "2025-07-19",
    }

    message = JobMessageBuilder.build(job)

    assert "💰 Salary" not in message
    assert "🔗" not in message
    assert "📌 Status: Part Time" in message
    assert "🏠 Arrangement: Onsite" in message


def test_build_defaults_and_fallbacks():
    job = {}  # completely empty job dictionary
    message = JobMessageBuilder.build(job)

    assert "📋 <b>No Title</b>" in message
    assert "🏢 <i>Unknown Company</i>" in message
    assert "🌍 Location: Unknown" in message
    assert "🏠 Arrangement: Onsite" in message
    assert "📌 Status: Not Specified" in message


def test_build_with_max_salary_only():
    job = {
        "job_title": "Support Engineer",
        "employer_name": "Zoho",
        "job_max_salary": 5000,
        "job_salary_period": "month",
        "job_posted_at": "2025-07-18",
    }

    message = JobMessageBuilder.build(job)

    assert "💰 Salary: Up to $5,000" in message


def test_build_with_salary_but_no_period():
    job = {
        "job_title": "Product Analyst",
        "employer_name": "Stripe",
        "job_min_salary": 8000,
        "job_max_salary": 12000,
        "job_salary_period": None,
        "job_posted_at": "2025-07-17",
    }

    message = JobMessageBuilder.build(job)

    assert "💰 Salary: $8,000 – $12,000" in message
    assert "per" not in message  # No period line
