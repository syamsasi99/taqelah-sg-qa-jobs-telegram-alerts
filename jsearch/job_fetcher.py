# job_notifier/api/job_fetcher.py

"""
This module handles interaction with external job search APIs using:
- Dependency Injection (host, headers)
- Separation of concerns (fetching vs processing)
- Error handling
"""

import time
from typing import Dict, List

import requests

from utils.logger import get_logger

logger = get_logger(__name__)


class JobFetcher:
    def __init__(self, api_host: str, api_key: str,
                 retries: int = 2, backoff_seconds: float = 2.0):
        self.api_host = api_host
        self.api_key = api_key
        self.retries = retries
        self.backoff_seconds = backoff_seconds
        # Number of queries that exhausted their retries. Lets the caller tell
        # "the API is down" apart from "there genuinely are no jobs today".
        self.error_count = 0
        self.base_url = f"https://{self.api_host}/search"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host
        }

    def fetch(self, query: str, country: str = "sg", page: int = 1,
              num_pages: int = 1, date_posted: str = "today") -> List[Dict]:
        logger.info("Getting jobs with query %s", query)
        params = {
            "query": query,
            "page": page,
            "num_pages": num_pages,
            "country": country,
            "date_posted": date_posted
        }

        last_error = None
        for attempt in range(self.retries + 1):
            try:
                response = requests.get(self.base_url, headers=self.headers,
                                        params=params, timeout=10)
                response.raise_for_status()
                return response.json().get("data", [])
            except requests.RequestException as error:
                last_error = error
                if attempt < self.retries:
                    delay = self.backoff_seconds * (attempt + 1)
                    logger.warning("Attempt %d/%d failed (%s), retrying in %gs",
                                   attempt + 1, self.retries + 1, error, delay)
                    time.sleep(delay)

        self.error_count += 1
        logger.error("❌ Error fetching jobs: %s", last_error)
        return []
