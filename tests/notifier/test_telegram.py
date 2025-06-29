import pytest
import requests

from notifier.telegram import TelegramNotifier


@pytest.fixture
def notifier():
    return TelegramNotifier(bot_token="dummy_token", chat_id="123456")


def test_send_success(requests_mock, notifier):
    mock_url = "https://api.telegram.org/botdummy_token/sendMessage"
    requests_mock.post(mock_url, json={"ok": True}, status_code=200)

    result = notifier.send("Test message")
    assert result is True


def test_send_failure_status_code(requests_mock, notifier):
    mock_url = "https://api.telegram.org/botdummy_token/sendMessage"
    requests_mock.post(mock_url, json={"ok": False, "description": "Bad Request"}, status_code=400)

    result = notifier.send("Test message")
    assert result is False


def test_send_exception(monkeypatch, notifier):
    def mock_post(*args, **kwargs):
        raise requests.RequestException("Connection error")

    monkeypatch.setattr(requests, "post", mock_post)
    result = notifier.send("Test message")
    assert result is False
