
from builder.job_messsage import JobMessageBuilder


def test_get_source_with_valid_urls():
    assert JobMessageBuilder.get_source("https://www.example.com/apply") == "example.com"
    assert JobMessageBuilder.get_source("http://careers.google.com") == "careers.google.com"
    assert JobMessageBuilder.get_source("https://linkedin.com/jobs/view/123456") == "linkedin.com"


def test_build_message_single_link():
    job = (
        "1",  # job_id (ignored)
        "QA Engineer",
        "TechCorp Inc.",
        "Singapore",
        "https://jobs.techcorp.com/apply",  # links
        "2024-06-28"
    )

    result = JobMessageBuilder.build(job)

    assert "📋 <b>QA Engineer</b>" in result
    assert "🏢 <i>TechCorp Inc.</i>" in result
    assert "🕒 Posted: 2024-06-28" in result
    assert "<a href='https://jobs.techcorp.com/apply'>jobs.techcorp.com</a>" in result


def test_build_message_multiple_links():
    job = (
        "2",
        "Test Engineer",
        "Innovate Ltd",
        "Remote",
        "https://apply.innovate.com/job123, https://careers.innovate.com/opening456",
        "2024-06-29"
    )

    result = JobMessageBuilder.build(job)

    assert "📋 <b>Test Engineer</b>" in result
    assert "🏢 <i>Innovate Ltd</i>" in result
    assert "🕒 Posted: 2024-06-29" in result
    assert "<a href='https://apply.innovate.com/job123'>apply.innovate.com</a>" in result
    assert "<a href='https://careers.innovate.com/opening456'>careers.innovate.com</a>" in result
