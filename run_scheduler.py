import time

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from tradezint.config import get_settings
from tradezint.jobs import generate_report_job, send_latest_reports
from tradezint.store import Store

load_dotenv()

settings = get_settings()
store = Store(settings.database_path)
store.init_db()


def generate_morning_reports():
    generate_report_job("nifty", store, settings)
    generate_report_job("fno", store, settings)


def send_morning_reports_and_generate_intraday():
    send_latest_reports("nifty", store, settings)
    send_latest_reports("fno", store, settings)
    generate_report_job("intraday", store, settings)


def send_intraday_report():
    send_latest_reports("intraday", store, settings)


if __name__ == "__main__":
    scheduler = BackgroundScheduler(timezone=settings.timezone)
    scheduler.add_job(generate_morning_reports, "cron", day_of_week="mon-fri", hour=8, minute=0)
    scheduler.add_job(send_morning_reports_and_generate_intraday, "cron", day_of_week="mon-fri", hour=9, minute=0)
    scheduler.add_job(send_intraday_report, "cron", day_of_week="mon-fri", hour=9, minute=30)
    scheduler.start()
    print("TradeZint scheduler running in Asia/Kolkata.")
    try:
        while True:
            time.sleep(30)
    except KeyboardInterrupt:
        scheduler.shutdown()
