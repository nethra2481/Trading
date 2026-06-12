import os
import time
import schedule
import glob
import datetime
from dotenv import load_dotenv

import data_ingestion
import analysis
import reporting
import subscribers

load_dotenv()
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
subscribers.init_db()

# We'll store the generated filenames in memory so the email jobs know what to send
generated_files = {
    'nifty': None,
    'fno': None,
    'intraday': None
}

def get_recipients():
    recipients = subscribers.get_active_emails()
    if recipients:
        return recipients
    # Fallback for initial setup compatibility.
    load_dotenv(override=True)
    single = os.getenv('CLIENT_EMAIL', EMAIL_ADDRESS)
    return [single] if single else []

def send_with_retry(report_type, subject, body, attachment_path, run_date):
    recipients = get_recipients()
    for recipient in recipients:
        success = False
        last_error = None
        for attempt in range(1, 4):
            ok, err = reporting.send_email(subject, body, attachment_path, recipient)
            if ok:
                success = True
                break
            last_error = err
            print(f"Retry {attempt}/3 failed for {recipient} [{report_type}]: {err}")
            time.sleep(2)

        if success:
            subscribers.log_delivery(run_date, report_type, recipient, subject, "SUCCESS")
        else:
            subscribers.log_delivery(run_date, report_type, recipient, subject, "FAILED", last_error)

def format_video_digest(videos):
    if not videos:
        return "No videos found."
    lines = []
    for idx, v in enumerate(videos[:5], start=1):
        title = v.get("title", "Untitled")
        published = v.get("published_at", "")
        vid = v.get("id", "")
        lines.append(f"{idx}. {title} | Published: {published} | Video ID: {vid}")
    return "\n".join(lines)

def today_report_filename(prefix):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    return f"{prefix}_Daily_Analysis_{date_str}.pdf"

def purge_old_reports():
    """Keep only today's report PDFs and remove older ones."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    patterns = [
        "Nifty_Daily_Analysis_*.pdf",
        "FNO_Daily_Analysis_*.pdf",
        "Intraday_Daily_Analysis_*.pdf",
    ]
    for pattern in patterns:
        for filepath in glob.glob(pattern):
            if not filepath.endswith(f"_{today}.pdf"):
                try:
                    os.remove(filepath)
                    print(f"Removed old report: {filepath}")
                except OSError as e:
                    print(f"Failed to remove old report {filepath}: {e}")

def job_8am_generate_nifty_fno():
    try:
        print("--- Running 8:00 AM Job: Fetching Data and Generating Nifty/FNO Reports ---")
        purge_old_reports()
        
        # 1. Fetch Shared Market Data
        market_data = data_ingestion.get_market_data()
        gift_nifty = data_ingestion.get_gift_nifty()
        
        # --- NIFTY REPORT ---
        print("Processing Nifty Analysis...")
        nifty_news = data_ingestion.get_news("Nifty 50 OR Nifty Index Option", max_results=25)
        nifty_videos = data_ingestion.get_top_youtube_videos("Nifty Index Option Trading Analysis Today", max_results=5)
        nifty_transcripts = data_ingestion.get_video_transcripts(nifty_videos)
        nifty_video_digest = format_video_digest(nifty_videos)
        
        nifty_report_text = analysis.analyze_nifty(nifty_transcripts, nifty_news, market_data, gift_nifty, nifty_video_digest)
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        nifty_filename = today_report_filename("Nifty")
        reporting.create_pdf(nifty_report_text, nifty_filename, f"Daily Nifty Index Option Analysis ({date_str})")
        generated_files['nifty'] = nifty_filename
        print(f"Saved {nifty_filename}")
        
        # --- FNO REPORT ---
        print("Processing FNO Analysis...")
        fno_news = data_ingestion.get_news("Indian Stock Market FNO Option Trading", max_results=25)
        fno_videos = data_ingestion.get_top_youtube_videos("FNO Stock Option Trading Analysis Today", max_results=5)
        fno_transcripts = data_ingestion.get_video_transcripts(fno_videos)
        fno_video_digest = format_video_digest(fno_videos)
        
        fno_report_text = analysis.analyze_fno(fno_transcripts, fno_news, market_data, gift_nifty, fno_video_digest)
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        fno_filename = today_report_filename("FNO")
        reporting.create_pdf(fno_report_text, fno_filename, f"Daily FNO Stock Trading Analysis ({date_str})")
        generated_files['fno'] = fno_filename
        print(f"Saved {fno_filename}")
        
        print("--- 8:00 AM Job Completed ---")
    except Exception as e:
        print(f"ERROR in 8:00 AM Job: {e}")

def job_9am_send_nifty_fno_and_generate_intraday():
    try:
        print("--- Running 9:00 AM Job: Sending Nifty/FNO and Generating CNBC Awaaz Report ---")
        purge_old_reports()
        
        run_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # 1. Send previously generated reports
        nifty_file = generated_files['nifty'] or today_report_filename("Nifty")
        fno_file = generated_files['fno'] or today_report_filename("FNO")
        if os.path.exists(nifty_file):
            send_with_retry(
                "NIFTY",
                "Nifty Daily Trading Analysis", 
                "Please find the Nifty daily analysis attached.", 
                nifty_file,
                run_date
            )
        if os.path.exists(fno_file):
            send_with_retry(
                "FNO",
                "FNO Daily Trading Analysis", 
                "Please find the FNO daily analysis attached.", 
                fno_file,
                run_date
            )
        
        # 2. Process CNBC Awaaz (We simulate getting the last 2 hours transcript)
        print("Processing CNBC Awaaz Live...")
        # In a real scenario, this might involve downloading a stream or finding the latest video on their channel.
        # For now, we search for their latest morning live stream.
        cnbc_videos = data_ingestion.get_top_youtube_videos("CNBC Awaaz Live", max_results=1)
        cnbc_transcript = "No transcript found for CNBC Awaaz."
        cnbc_video_digest = format_video_digest(cnbc_videos)
        if cnbc_videos:
            cnbc_transcript = data_ingestion.get_video_transcripts(cnbc_videos)
        
        intraday_report_text = analysis.analyze_intraday(cnbc_transcript, cnbc_video_digest)
        intraday_filename = today_report_filename("Intraday")
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        reporting.create_pdf(intraday_report_text, intraday_filename, f"Daily Intraday Trading Analysis (CNBC Awaaz - {date_str})")
        generated_files['intraday'] = intraday_filename
        print(f"Saved {intraday_filename}")
        
        print("--- 9:00 AM Job Completed ---")
    except Exception as e:
        print(f"ERROR in 9:00 AM Job: {e}")

def job_930am_send_intraday():
    try:
        print("--- Running 9:30 AM Job: Sending CNBC Awaaz Report ---")
        
        run_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        intraday_file = generated_files['intraday'] or today_report_filename("Intraday")
        if os.path.exists(intraday_file):
            send_with_retry(
                "INTRADAY",
                "CNBC Awaaz Intraday Analysis", 
                "Please find the Intraday/Scalping analysis attached.", 
                intraday_file,
                run_date
            )
        
        print("--- 9:30 AM Job Completed ---")
    except Exception as e:
        print(f"ERROR in 9:30 AM Job: {e}")

if __name__ == "__main__":
    print("Scheduling Daily Trading Analysis Jobs...")
    
    # Schedule the jobs in IST timezone. 
    # NOTE: The system running this script needs to have its timezone set to IST, 
    # or the times below need to be adjusted to UTC or the server's local time.
    
    schedule.every().day.at("08:00").do(job_8am_generate_nifty_fno)
    schedule.every().day.at("09:00").do(job_9am_send_nifty_fno_and_generate_intraday)
    schedule.every().day.at("09:30").do(job_930am_send_intraday)
    
    print("Scheduler is running. Press Ctrl+C to exit.")
    
    # Run a test immediately to ensure everything works (Uncomment to test)
    # print("Running a test cycle immediately...")
    # job_8am_generate_nifty_fno()
    # job_9am_send_nifty_fno_and_generate_intraday()
    # job_930am_send_intraday()

    while True:
        schedule.run_pending()
        time.sleep(60)
