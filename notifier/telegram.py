"""Telegram notifier module."""

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

    def send(self, message):
        """
        Send a message to the Telegram chat.

        Args:
            message (str): The message to send.

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

            logger.warning("❌ Failed to send: %s - %s", response.status_code, response.text)
        except requests.RequestException as error:
            logger.error("❌ Error sending message: %s", error)

        return False
