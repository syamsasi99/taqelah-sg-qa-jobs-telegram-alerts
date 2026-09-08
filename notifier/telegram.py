"""Telegram notifier module."""

import time

import requests
from utils.logger import get_logger

logger = get_logger(__name__)


class TelegramNotifier:
    """Sends messages to a Telegram chat via bot API."""

    def __init__(self, bot_token, chat_id):
        """
        Initialize the notifier.

        Args:
            bot_token (str): Telegram bot token.
            chat_id (str): Telegram chat ID.
        """
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send(self, message, retry_on_rate_limit=True):
        """
        Send a message to the Telegram chat.

        Args:
            message (str): The message to send.
            retry_on_rate_limit (bool): Honour a 429 by sleeping for the
                retry_after Telegram reports, then trying once more.

        Returns:
            bool: True if sent successfully, False otherwise.
        """
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info("✅ Message sent.")
                return True

            if response.status_code == 429 and retry_on_rate_limit:
                wait = self._retry_after(response)
                logger.warning("Rate limited, waiting %ds before one retry.", wait)
                time.sleep(wait)
                return self.send(message, retry_on_rate_limit=False)

            logger.warning("❌ Failed to send: %s - %s", response.status_code, response.text)
        except requests.RequestException as error:
            logger.error("❌ Error sending message: %s", error)

        return False

    @staticmethod
    def _retry_after(response, default=5):
        """Seconds Telegram asks us to wait, per its 429 payload."""
        try:
            return int(response.json()["parameters"]["retry_after"])
        except (ValueError, KeyError, TypeError):
            return default
