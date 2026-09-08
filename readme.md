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

Copy the template and fill it in. `.env` is gitignored - never commit real values.

```bash
cp .env.example .env
```

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
CHAT_ID=your_chat_id          # group IDs are negative, e.g. -1001234567890
RAPIDAPI_KEY=your_rapidapi_key
```

Real environment variables take precedence over `.env`, so CI secrets always win.

### 4. Run the notifier

```bash
python main.py
```

Point `CHAT_ID` at a **test group** when running locally. Optional overrides:

| Variable | Default | Purpose |
|---|---|---|
| `RECENT_WINDOW_HOURS` | `48` | How old a job may be and still be sent |
| `MAX_JOBS` | `30` | Max unsent jobs dispatched per run |
| `SEND_DELAY_SECONDS` | `1` | Pause between Telegram sends |
| `DB_FILE` | `jobs.db` | SQLite ledger location |

---

## 🧱 Project Structure

```
taqelah-sg-qa-jobs-telegram-alerts/
├── jsearch/
│   └── job_fetcher.py         # External API communication
├── builder/
│   └── job_messsage.py        # Message formatting (Builder pattern)
├── db/
│   └── repository.py          # Sent-job ledger (Repository pattern)
├── notifier/
│   └── telegram.py            # Telegram adapter
├── utils/
│   └── logger.py              # Shared logger
├── tests/                     # pytest suite
├── main.py                    # Orchestrator and filtering
```

---

## 🧪 Sample Job Flow

```text
1. Fetch jobs from JSearch API (4 queries)
2. Keep jobs whose TITLE names a software QA/test role
3. Drop non-software test domains (test cells, semiconductor, calibration)
4. Keep jobs posted within RECENT_WINDOW_HOURS, by epoch timestamp
5. Insert into SQLite; the job_id primary key drops repeats
6. Send only jobs still marked unsent, then mark them sent
```

> ⚠️ Recency is filtered on `job_posted_at_timestamp`, **not** the human-readable
> `job_posted_at` string. JSearch's index lags real posting time by ~29-46 hours,
> so `job_posted_at` is never "N hours ago" - matching that string silently
> dropped 100% of jobs for two weeks. The 48h window means a job can appear in
> two consecutive daily runs, which is exactly why the SQLite ledger must
> persist between runs (see the cache step in the workflow).

---

## 📌 Requirements

```text
- Python 3.11+
- requests
- python-dotenv
- pytest, requests-mock (tests)
```

Run the tests with:

```bash
pytest tests -q
```

---

## 📝 License

MIT

---

## 📬 Contact

For questions or enhancements, open an issue or contact [@syam](https://github.com/syamsasi99)