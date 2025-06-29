import pytest
from unittest.mock import patch, MagicMock

from jsearch.job_fetcher import JobFetcher

API_HOST = "fake-job-api.p.rapidapi.com"
API_KEY = "fake-api-key"

@pytest.fixture
def job_fetcher():
    return JobFetcher(api_host=API_HOST, api_key=API_KEY)


@patch("jsearch.job_fetcher.requests.get")
def test_fetch_success(mock_get, job_fetcher):
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"job_id": "123", "job_title": "QA Engineer"},
            {"job_id": "456", "job_title": "Test Engineer"}
        ]
    }
    mock_get.return_value = mock_response

    # Act
    results = job_fetcher.fetch(query="qa engineer")

    # Assert
    assert isinstance(results, list)
    assert len(results) == 2
    assert results[0]["job_title"] == "QA Engineer"
    mock_get.assert_called_once()


@patch("jsearch.job_fetcher.requests.get")
def test_fetch_empty_data(mock_get, job_fetcher):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": []}
    mock_get.return_value = mock_response

    results = job_fetcher.fetch(query="nonexistent job")

    assert isinstance(results, list)
    assert results == []