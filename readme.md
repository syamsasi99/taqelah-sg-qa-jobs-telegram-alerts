# QA Job Notifier Bot

This Python project fetches QA/Test Engineer job listings from the JSearch RapidAPI and sends notifications to a Telegram channel or group.

---

## 📦 Features

- Fetch latest job listings using JSearch API  
- Store job entries in a local SQLite database  
- Prevent duplicate job notifications  
- Send formatted messages to Telegram via Bot API  
- Modular structure with design patterns (Repository, Adapter, Builder)

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone git@github.com:syamsasi99/taqelah-sg-qa-jobs-telegram-alerts.git
cd taqelah-sg-qa-jobs-telegram-alerts
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variables

```bash
export TELEGRAM_BOT_TOKEN=your_telegram_bot_token
export CHAT_ID=your_chat_id
export RAPIDAPI_KEY=your_rapidapi_key
```

> 💡 You can also use a `.env` file with `python-dotenv`:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
CHAT_ID=your_chat_id
RAPIDAPI_KEY=your_rapidapi_key
```

### 4. Run the notifier

```bash
python -m main.py
```

---

## 🧱 Project Structure

```
job_notifier/
├── api/
│   └── job_fetcher.py         # External API communication
├── builder/
│   └── job_message.py         # Message formatting (Builder pattern)
├── db/
│   └── repository.py          # DB access (Repository pattern)
├── notifier/
│   └── telegram.py            # Telegram adapter
├── utils/
│   └── logger.py              # Shared logger
├── config.py                  # Constants and configuration
├── main.py                    # Orchestrator
```

---

## 🧪 Sample Job Flow

```text
1. Fetch jobs from JSearch API  
2. Insert unique jobs into SQLite  
3. Identify unsent jobs  
4. Send each job to Telegram  
5. Mark job as sent  
```

---

## 📌 Requirements

```text
- Python 3.8+
- requests
- python-dotenv
```

---

## 📝 License

MIT

---

## 📬 Contact

For questions or enhancements, open an issue or contact [@syam](https://github.com/syamsasi99)