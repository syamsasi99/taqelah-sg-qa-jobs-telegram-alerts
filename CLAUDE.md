# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A once-daily GitHub Actions cron job. It queries the JSearch RapidAPI for QA/test-engineer
roles in Singapore, filters them, and posts one Telegram message per job. There is no server
and no long-lived process — `main.py` runs to completion and exits.

## Commands

```bash
# Setup (system python3 is macOS 3.9 with no pytest; CI uses 3.11)
python3.12 -m venv .venv && ./.venv/bin/pip install -r requirements.txt

./.venv/bin/python -m pytest tests -q            # full suite
./.venv/bin/python -m pytest tests/test_main.py -q
./.venv/bin/python -m pytest tests/test_main.py::test_is_recent_window -q
./.venv/bin/python -m pytest tests -q -k recent  # by name

./.venv/bin/python main.py                       # full pipeline, SENDS REAL MESSAGES
```

`main.py` reads credentials from `.env` via `python-dotenv` (`cp .env.example .env`). Real
environment variables override `.env`, so CI secrets always win.

**Always point `CHAT_ID` at a test group before running `main.py` locally.** It sends
immediately with no dry-run flag and no confirmation.

Behaviour overrides: `RECENT_WINDOW_HOURS` (48), `MAX_JOBS` (30), `SEND_DELAY_SECONDS` (1),
`DB_FILE` (`jobs.db`).

## Architecture

`main.py` is the orchestrator; every other module is a single small class it composes.

```
JobFetcher.fetch() x4 queries   jsearch/job_fetcher.py
  -> filter_software_jobs()     main.py         keyword AND recency
  -> dedupe by job_id           main.py         within one run
  -> JobRepository.insert_jobs  db/repository.py job_id PRIMARY KEY drops repeats
  -> fetch_unsent_jobs          db/repository.py across runs
  -> JobMessageBuilder.build    builder/job_messsage.py
  -> TelegramNotifier.send      notifier/telegram.py
  -> mark_as_sent               only on a successful send
```

The SQLite table stores only enough to be a **ledger** (`job_id` + `is_sent`), not enough to
rebuild a message. Messages are always built from the freshly fetched dicts; the DB is
consulted purely to answer "have I already sent this `job_id`?". Keep that split — widening
the schema to render messages from the DB would mean backfilling every field the builder
reads.

## Domain constraints that are easy to get wrong

**Never filter recency on `job_posted_at`.** It is a human-readable string
(`"1 day ago"`, `"Just posted"`, `"Today"`). JSearch's index lags real posting time by
roughly 29–46 hours, so **nothing the API returns is ever under 24h old** — measured across
`date_posted=today|3days|week`, zero jobs at `<=24h`. A previous filter matched
`"hours"`/`"minutes"` in that string and silently dropped 100% of jobs for two weeks while
every CI run stayed green. Use the `job_posted_at_timestamp` epoch field. `tests/test_main.py`
pins this as a regression.

**The 48h window and the ledger are coupled.** A window wider than the 24h cron interval means
a job matches on two consecutive runs. Dedupe via `JobRepository` is what makes that safe —
don't disable one without reconsidering the other.

**Telegram uses `parse_mode: HTML`.** Every interpolated field in `JobMessageBuilder.build`
must go through `html.escape()`. An unescaped `&` or `<` in a job title makes Telegram reject
the entire message with a 400, and the listing is lost silently.

**Silent failure is this repo's recurring bug class.** `JobFetcher.fetch` returns `[]` on
error, which is indistinguishable from "no jobs" unless you check `fetcher.error_count`.
`main()` returns an exit code and logs a stage funnel
(`fetched N -> keyword M -> recent K`) for exactly this reason. When adding a filter or a
network call, make the failure observable rather than letting it collapse into an empty list.

## CI

`.github/workflows/run-script.yml` — cron `00 00 * * *` plus manual dispatch with a
staging/production choice. GitHub's scheduler routinely delays this by hours; nothing may
depend on the run's wall-clock time.

**Environment secrets.** The job must declare `environment:` for the environment whose secrets
it wants — GitHub injects only that environment's secrets. The chat target resolves as
`CHAT_ID || PROD_CHAT_ID || STAGING_CHAT_ID`, so either naming works; `BOT_TOKEN` and
`RAPIDAPI_KEY` are repo-level.

**The ledger survives via `actions/cache`.** `actions/cache` never overwrites an existing key,
so the key rotates per run (`jobs-db-<env>-<run_id>`) with a prefix `restore-keys`. The
environment is part of the prefix — a shared ledger would let a staging dispatch mark jobs
sent and suppress them in production. Caches untouched for 7 days are evicted, after which a
run re-sends everything inside the window.

No workflow runs on `pull_request`, so tests do not gate merges — verify locally.

## Conventions

- `utils.logger.get_logger(__name__)` in every module; `%s` lazy formatting, not f-strings.
- `builder/job_messsage.py` is misspelled (three `s`). Renaming touches imports and tests.
- Tests mirror the package layout under `tests/`, except `tests/test_main.py`.
