# TradeZint Daily Trading Analysis

TradeZint is a Flask web app that automates daily Indian options research and PDF delivery.

It produces:

- Nifty Index option analysis for the nearest weekly expiry by 9:00 AM IST.
- FNO stock option analysis for the nearest monthly expiry by 9:00 AM IST.
- CNBC Awaaz intraday and scalping analysis by 9:30 AM IST.

Each trading report is built from recent YouTube videos, news, and the 8:00 AM IST macro snapshot: Gift Nifty, Dow Jones Futures, Crude Oil, Dollar Index, US 10-Year Bond Yield, and India VIX. PDFs include CE/PE buy-sell legs, maximum profit, maximum risk, expiry view, levels, and risk disclosure.

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Open `http://127.0.0.1:5000`.

## Run Scheduler

```bash
python run_scheduler.py
```

Scheduled jobs use `Asia/Kolkata`:

- 08:00: capture data and generate Nifty + FNO PDFs.
- 09:00: email Nifty + FNO PDFs and generate intraday PDF.
- 09:30: email intraday PDF.

## Environment

Set these in `.env` for full automation:

- `GEMINI_API_KEY`
- `YOUTUBE_API_KEY`
- `EMAIL_ADDRESS`
- `EMAIL_APP_PASSWORD`

Without those keys, the app still runs and shows degraded readiness. Report generation falls back to clearly marked unavailable sections.

## Risk Disclosure

This product creates educational market research only. It is not SEBI registered investment advice. Options and futures trading involve substantial risk.
