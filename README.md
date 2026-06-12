# TradeZint - Advanced Algorithmic Trading Analytics Platform

TradeZint is a fully automated, cloud-hosted, AI-driven quantitative trading analysis platform designed specifically for the Indian Stock Market. It utilizes advanced data ingestion, real-time macro indicators, and Google Gemini 2.5 Flash to generate highly accurate, actionable Daily Option Trading PDFs directly to user inboxes.

## 🚀 Key Features

### 1. 100% Automated Daily PDF Reports (IST Timed)
- **8:00 AM IST (Nifty Index Options):** Analyzes the Top 5 YouTube videos, news, and live global macros to output Best Buy/Sell Option Legs for CE/PE (Nearest Weekly Expiry) with calculated Max Profit and Risk.
- **8:00 AM IST (FNO Stock Options):** Generates identical actionable Option Leg strategies for the Nearest Monthly Expiry.
- **9:30 AM IST (Intraday Option Scalping):** Specifically targets the *CNBC Awaaz Morning Live Pehla Sauda* broadcast (7 AM - 9 AM) to formulate rapid intraday option scalping strategies.
- **Weekend Awareness:** The system detects Saturdays and Sundays, automatically skipping PDF generation and instead sending a "Market Closed" notification to all subscribed users.

### 2. Live Global Macro Data Ingestion
To accurately price option premiums, the system dynamically fetches real-time data at 8:00 AM using `yfinance` before AI generation:
- **India VIX (^INDIAVIX)** for implied volatility and premium pricing.
- **Gift Nifty** for opening gap up/down sentiment.
- **Dow Jones Futures (YM=F)**
- **Crude Oil (CL=F)**
- **US Dollar Index (DX-Y.NYB)**
- **US 10-Yr Bond Yield (^TNX)**

### 3. Professional Frontend Dashboard
The user-facing website is engineered to replicate premium financial platforms (like Zerodha or TradingView):
- **Live Market Ticker:** Real-time scrolling ticker tape for Sensex, Nifty 50, and Bank Nifty.
- **Advanced Interactive Chart:** Deep, fully-interactive TradingView charting system mapped to Nifty.
- **Ultimate Trader Toolkit:** Embedded global Macro Economic Calendars, Nifty 50 Technical Gauges, and Market Heatmaps.
- **Glassmorphism UI:** Stunning dark-mode aesthetics with animated gradients, glass panels, and a strict Professional SEBI/Risk Disclaimer footer.

### 4. Robust Cloud Backend Architecture
- **Web Server:** Flask / Gunicorn hosted continuously on Render.
- **Database:** Fully-managed, permanent PostgreSQL database provided by Neon serverless Postgres.
- **Email System:** SMTP integration via Google App Passwords capable of distributing PDFs to a multi-subscriber database securely.
- **Automated Scheduling:** Python `schedule` running natively in `Asia/Kolkata` timezone, kept continuously awake via a pinging cron-bot.

## 🛠 Tech Stack
- **Backend:** Python 3, Flask, SQLAlchemy, Schedule
- **Database:** PostgreSQL (Neon Serverless)
- **AI/ML:** Google GenAI SDK (Gemini 2.5 Flash)
- **Data Scraping:** yfinance, Google API (YouTube Data v3), YouTube Transcript API, BeautifulSoup, GNews
- **Frontend:** HTML5, Vanilla CSS3 (Glassmorphism), JavaScript, TradingView Widgets

## ⚙️ Environment Variables
To run this project locally or deploy it to the cloud, the following `.env` variables must be configured:
```env
# Google Services
GEMINI_API_KEY=your_gemini_api_key
YOUTUBE_API_KEY=your_youtube_api_key

# Email Infrastructure
EMAIL_ADDRESS=your_sender_email@gmail.com
EMAIL_APP_PASSWORD=your_google_app_password

# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:password@endpoint.neon.tech/dbname?sslmode=require

# Settings
USE_YT_TRANSCRIPTS=true
```

## ⚠️ Disclaimer
All generated reports and strategies are for educational and analytical purposes only. Option trading involves significant financial risk. The platform strictly enforces automated SEBI risk warnings and assumes no liability for trading losses.
