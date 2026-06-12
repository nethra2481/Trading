import os
import time
import schedule
import datetime
import data_ingestion
import analysis
import reporting
import subscribers
from dotenv import load_dotenv

load_dotenv()
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
subscribers.init_db()

# In-memory store for generated filenames/bytes during a session
generated = {
    'nifty_file': None,
    'nifty_bytes': None,
    'fno_file': None,
    'fno_bytes': None,
    'intraday_file': None,
    'intraday_bytes': None,
}


def get_recipients():
    recipients = subscribers.get_active_emails()
    if recipients:
        return recipients
    load_dotenv(override=True)
    single = os.getenv('CLIENT_EMAIL', EMAIL_ADDRESS)
    return [single] if single else []


def send_with_retry(report_type, subject, body, filename, pdf_bytes, run_date):
    """Send email with up to 3 retries per recipient."""
    recipients = get_recipients()
    for recipient in recipients:
        success = False
        last_error = None
        for attempt in range(1, 4):
            ok, err = reporting.send_email(subject, body, filename, recipient, pdf_bytes=pdf_bytes)
            if ok:
                success = True
                break
            last_error = err
            print(f"  Retry {attempt}/3 for {recipient}: {err}")
            time.sleep(3)

        status = "SUCCESS" if success else "FAILED"
        subscribers.log_delivery(run_date, report_type, recipient, subject, status, None if success else last_error)
        print(f"  [{status}] {report_type} → {recipient}")


def format_video_digest(videos):
    if not videos:
        return "No videos found."
    lines = []
    for idx, v in enumerate(videos[:5], 1):
        title = v.get("title", "Untitled")
        channel = v.get("channel", "Unknown Channel")
        published = v.get("published_at", "")[:10]
        vid_id = v.get("id", "")
        url = f"https://www.youtube.com/watch?v={vid_id}" if vid_id else ""
        lines.append(f"{idx}. [{channel}] {title} (Published: {published}) {url}")
    return "\n".join(lines)


def today_str():
    return datetime.datetime.now().strftime("%Y-%m-%d")


def today_filename(prefix):
    return f"{prefix}_Option_Analysis_{today_str()}.pdf"


def build_email_body(report_type, date_str, market_data=None, gift_nifty=None):
    """Build a professional, informative email body for each report type."""
    mkt_lines = ""
    if market_data:
        mkt_lines = "\n".join([f"  • {k}: {v}" for k, v in market_data.items()])
        mkt_lines = f"\n\nMarket Snapshot (8:00 AM IST):\n{mkt_lines}\n  • Gift Nifty: {gift_nifty}"

    if report_type == "NIFTY":
        return f"""Dear Trader,

Please find attached your Daily Nifty Index Option Analysis for {date_str}.

This report includes:
  ✅ Global Market Summary (Dow Futures, Crude, DXY, US Bond Yield, Gift Nifty)
  ✅ India VIX & Volatility Analysis
  ✅ Overall View for the Nearest Weekly Expiry
  ✅ CE/PE Strategies in Leg Format (Strike, Premium, Entry, Target, SL)
  ✅ Maximum Profit & Risk per Strategy
  ✅ Key Levels (Support, Resistance, Max Pain, Pivot){mkt_lines}

Analysis generated using Gemini 2.5 Flash AI based on:
  - Top 5 YouTube Nifty Option Analysis videos
  - Latest news from NSE/Indian market sources
  - Real-time global market data captured at 8:00 AM IST

DISCLAIMER: This analysis is for educational and informational purposes only.
Not SEBI registered advice. Trade at your own risk.

Best regards,
TradeZint Algorithmic Analytics
"""

    elif report_type == "FNO":
        return f"""Dear Trader,

Please find attached your Daily FNO Stock Option Analysis for {date_str}.

This report includes:
  ✅ Global Market Summary (Dow Futures, Crude, DXY, US Bond Yield, Gift Nifty)
  ✅ FNO Market Overview (BankNifty, FinNifty, F&O Ban List)
  ✅ Overall View for the Nearest Monthly Expiry
  ✅ CE/PE Strategies on FNO Stocks in Leg Format
  ✅ Maximum Profit & Risk per Strategy
  ✅ Top FNO Stocks to Watch{mkt_lines}

Analysis generated using Gemini 2.5 Flash AI based on:
  - Top 5 YouTube FNO Option Analysis videos
  - Latest FNO-related news
  - Real-time global market data captured at 8:00 AM IST

DISCLAIMER: This analysis is for educational and informational purposes only.
Not SEBI registered advice. Trade at your own risk.

Best regards,
TradeZint Algorithmic Analytics
"""

    elif report_type == "INTRADAY":
        return f"""Dear Trader,

Please find attached your Daily Intraday & Scalping Option Analysis for {date_str}.

This report is based on CNBC Awaaz Morning Live (7:00 AM – 9:00 AM IST) and includes:
  ✅ Morning Market Briefing (CNBC Awaaz expert views)
  ✅ Overall View for Daily Option Trading & Intraday Scalping
  ✅ Intraday CE/PE Strategies in Leg Format (Entry, Target, SL, Exit Time)
  ✅ Quick Scalping Setups (15–30 minute trades)
  ✅ Maximum Profit & Risk per Setup
  ✅ Intraday Key Levels (Nifty & Bank Nifty)

All intraday positions should be squared off before 3:20 PM IST.

DISCLAIMER: This analysis is for educational and informational purposes only.
Not SEBI registered advice. Trade at your own risk.

Best regards,
TradeZint Algorithmic Analytics
"""

    elif report_type == "WEEKEND":
        return """Dear Trader,

The Indian Stock Market (NSE/BSE) is CLOSED today as it is a weekend (Saturday/Sunday).

No option trading analysis has been generated today. Our AI systems will automatically resume full analysis on the next trading day (Monday).

You will receive:
  📧 Nifty Weekly Option Analysis — Monday 9:00 AM IST
  📧 FNO Monthly Option Analysis  — Monday 9:00 AM IST
  📧 Intraday Scalping Analysis   — Monday 9:30 AM IST

Have a great weekend!

Best regards,
TradeZint Algorithmic Analytics
"""
    return "Please find the attached report."


# ─────────────────────────────────────────────
# JOB 1: 8:00 AM IST — Fetch data, generate Nifty + FNO PDFs
# ─────────────────────────────────────────────

def job_8am_generate():
    if datetime.datetime.now().weekday() >= 5:
        print("--- Weekend: Skipping 8:00 AM generation job ---")
        return

    print("=" * 60)
    print("JOB 8:00 AM IST — Fetching market data & generating reports")
    print("=" * 60)

    try:
        # ── Shared market data ──
        print("  Fetching global market data...")
        market_data = data_ingestion.get_market_data()
        gift_nifty = data_ingestion.get_gift_nifty()
        print(f"  Market data: {market_data}")
        print(f"  Gift Nifty: {gift_nifty}")

        date_str = today_str()

        # ── NIFTY REPORT ──
        print("  [NIFTY] Fetching YouTube videos...")
        nifty_videos = data_ingestion.get_top_youtube_videos(
            "Nifty Index Option Trading Weekly Expiry Analysis Today CE PE",
            max_results=5
        )
        nifty_video_digest = format_video_digest(nifty_videos)
        nifty_transcripts = data_ingestion.get_video_transcripts(nifty_videos)

        print("  [NIFTY] Fetching news...")
        nifty_news = data_ingestion.get_all_nifty_news()

        print("  [NIFTY] Running AI analysis...")
        nifty_text = analysis.analyze_nifty(
            nifty_transcripts, nifty_news, market_data, gift_nifty, nifty_video_digest
        )

        nifty_file = today_filename("Nifty")
        nifty_title = f"TradeZint — Nifty Index Option Analysis — {date_str}"
        _, nifty_bytes = reporting.create_pdf(nifty_text, nifty_file, nifty_title)
        subscribers.save_report("Nifty", date_str, nifty_file, nifty_bytes)
        generated['nifty_file'] = nifty_file
        generated['nifty_bytes'] = nifty_bytes
        generated['nifty_market'] = market_data
        generated['gift_nifty'] = gift_nifty
        print(f"  [NIFTY] Report generated: {nifty_file}")

        # ── FNO REPORT ──
        print("  [FNO] Fetching YouTube videos...")
        fno_videos = data_ingestion.get_top_youtube_videos(
            "FNO Stock Option Trading Monthly Expiry Analysis Today CE PE NSE",
            max_results=5
        )
        fno_video_digest = format_video_digest(fno_videos)
        fno_transcripts = data_ingestion.get_video_transcripts(fno_videos)

        print("  [FNO] Fetching news...")
        fno_news = data_ingestion.get_all_fno_news()

        print("  [FNO] Running AI analysis...")
        fno_text = analysis.analyze_fno(
            fno_transcripts, fno_news, market_data, gift_nifty, fno_video_digest
        )

        fno_file = today_filename("FNO")
        fno_title = f"TradeZint — FNO Stock Option Analysis — {date_str}"
        _, fno_bytes = reporting.create_pdf(fno_text, fno_file, fno_title)
        subscribers.save_report("FNO", date_str, fno_file, fno_bytes)
        generated['fno_file'] = fno_file
        generated['fno_bytes'] = fno_bytes
        print(f"  [FNO] Report generated: {fno_file}")

        print("JOB 8:00 AM COMPLETE ✓")

    except Exception as e:
        print(f"ERROR in 8:00 AM job: {e}")
        import traceback
        traceback.print_exc()


# ─────────────────────────────────────────────
# JOB 2: 9:00 AM IST — Send Nifty+FNO PDFs & generate Intraday PDF
# ─────────────────────────────────────────────

def job_9am_send_and_generate_intraday():
    date_str = today_str()

    if datetime.datetime.now().weekday() >= 5:
        print("--- Weekend: Sending market closed notification ---")
        send_with_retry(
            "WEEKEND",
            f"TradeZint — Market Closed Today ({date_str})",
            build_email_body("WEEKEND", date_str),
            None, None,
            date_str
        )
        return

    print("=" * 60)
    print("JOB 9:00 AM IST — Sending Nifty/FNO & Generating Intraday")
    print("=" * 60)

    try:
        mkt = generated.get('nifty_market')
        gift = generated.get('gift_nifty')

        # ── Send Nifty report ──
        if generated['nifty_bytes']:
            send_with_retry(
                "NIFTY",
                f"TradeZint — Nifty Index Option Analysis ({date_str})",
                build_email_body("NIFTY", date_str, mkt, gift),
                generated['nifty_file'],
                generated['nifty_bytes'],
                date_str
            )
        else:
            print("  [NIFTY] No report available to send (8AM job may have failed)")

        # ── Send FNO report ──
        if generated['fno_bytes']:
            send_with_retry(
                "FNO",
                f"TradeZint — FNO Stock Option Analysis ({date_str})",
                build_email_body("FNO", date_str, mkt, gift),
                generated['fno_file'],
                generated['fno_bytes'],
                date_str
            )
        else:
            print("  [FNO] No report available to send (8AM job may have failed)")

        # ── Generate CNBC Awaaz intraday report ──
        print("  [INTRADAY] Fetching CNBC Awaaz morning videos...")
        cnbc_videos = data_ingestion.get_cnbc_awaaz_morning_video()
        if not cnbc_videos:
            # Fallback: general CNBC Awaaz search
            cnbc_videos = data_ingestion.get_top_youtube_videos(
                "CNBC Awaaz Morning Live Pehla Sauda intraday option trading", max_results=2, days_back=1
            )
        cnbc_digest = format_video_digest(cnbc_videos)
        cnbc_transcript = data_ingestion.get_video_transcripts(cnbc_videos)

        print("  [INTRADAY] Running AI analysis...")
        intraday_text = analysis.analyze_intraday(
            cnbc_transcript, cnbc_digest, market_data=mkt, gift_nifty=gift
        )

        intraday_file = today_filename("Intraday")
        intraday_title = f"TradeZint — Intraday & Scalping Option Analysis (CNBC Awaaz) — {date_str}"
        _, intraday_bytes = reporting.create_pdf(intraday_text, intraday_file, intraday_title)
        subscribers.save_report("Intraday", date_str, intraday_file, intraday_bytes)
        generated['intraday_file'] = intraday_file
        generated['intraday_bytes'] = intraday_bytes
        print(f"  [INTRADAY] Report generated: {intraday_file}")

        print("JOB 9:00 AM COMPLETE ✓")

    except Exception as e:
        print(f"ERROR in 9:00 AM job: {e}")
        import traceback
        traceback.print_exc()


# ─────────────────────────────────────────────
# JOB 3: 9:30 AM IST — Send Intraday PDF
# ─────────────────────────────────────────────

def job_930am_send_intraday():
    if datetime.datetime.now().weekday() >= 5:
        print("--- Weekend: Skipping 9:30 AM intraday job ---")
        return

    date_str = today_str()
    print("=" * 60)
    print("JOB 9:30 AM IST — Sending Intraday CNBC Awaaz Report")
    print("=" * 60)

    try:
        if generated['intraday_bytes']:
            send_with_retry(
                "INTRADAY",
                f"TradeZint — Intraday & Scalping Option Analysis ({date_str})",
                build_email_body("INTRADAY", date_str),
                generated['intraday_file'],
                generated['intraday_bytes'],
                date_str
            )
        else:
            print("  [INTRADAY] No report available (9:00 AM job may have failed)")

        print("JOB 9:30 AM COMPLETE ✓")

    except Exception as e:
        print(f"ERROR in 9:30 AM job: {e}")


# ─────────────────────────────────────────────
# ENTRYPOINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("TradeZint Scheduler Starting...")
    print("Scheduled jobs (IST):")
    print("  08:00 AM — Fetch market data, generate Nifty & FNO option reports")
    print("  09:00 AM — Email Nifty & FNO reports, generate Intraday CNBC Awaaz report")
    print("  09:30 AM — Email Intraday & Scalping report")
    print("")

    schedule.every().day.at("08:00", "Asia/Kolkata").do(job_8am_generate)
    schedule.every().day.at("09:00", "Asia/Kolkata").do(job_9am_send_and_generate_intraday)
    schedule.every().day.at("09:30", "Asia/Kolkata").do(job_930am_send_intraday)

    print("Scheduler running. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(30)
