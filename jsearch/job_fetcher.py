# job_notifier/api/job_fetcher.py

"""
This module handles interaction with external job search APIs using:
- Dependency Injection (host, headers)
- Separation of concerns (fetching vs processing)
- Error handling
"""

import requests
from typing import List, Dict
from utils.logger import get_logger

logger = get_logger(__name__)


class JobFetcher:
    def __init__(self, api_host: str, api_key: str):
        self.api_host = api_host
        self.api_key = api_key
        self.base_url = f"https://{self.api_host}/search"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host
        }

    def fetch(self, query: str, country: str = "sg", page: int = 1, num_pages: int = 1) -> List[Dict]:
        logger.info("Getting jobs with query %s",query)
        params = {
            "query": query,
            "page": page,
            "num_pages": num_pages,
            "country": country,
            "date_posted": "today"
        }

        try:
            response = requests.get(self.base_url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            json_data = response.json()
            return json_data.get("data", [])
        except requests.RequestException as e:
            logger.error(f"❌ Error fetching jobs: {e}")
            return []
