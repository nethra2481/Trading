from datetime import datetime

from tradezint.analysis import generate_analysis
from tradezint.data_sources import (
    get_market_snapshot,
    latest_news,
    transcript_text,
    video_digest,
    youtube_search,
)
from tradezint.emailer import send_pdf
from tradezint.reports import create_pdf


REPORT_CONFIG = {
    "nifty": {
        "category": "Nifty",
        "title": "TradeZint - Nifty Index Weekly Option Analysis",
        "query": "Nifty Index option trading weekly expiry analysis today CE PE",
        "news": "Nifty 50 options weekly expiry CE PE stock market India today",
    },
    "fno": {
        "category": "FNO",
        "title": "TradeZint - FNO Stock Monthly Option Analysis",
        "query": "FNO stock option trading monthly expiry analysis today CE PE NSE",
        "news": "NSE FNO stocks options monthly expiry F&O ban list today",
    },
    "intraday": {
        "category": "Intraday",
        "title": "TradeZint - CNBC Awaaz Intraday and Scalping Analysis",
        "query": "CNBC Awaaz morning live Pehla Sauda intraday option trading today",
        "news": "CNBC Awaaz stock market intraday trading Nifty Bank Nifty today",
    },
}


def generate_report_job(report_type, store, settings):
    config = REPORT_CONFIG[report_type]
    market = get_market_snapshot()
    videos = youtube_search(settings.youtube_api_key, config["query"], max_results=5)
    digest = video_digest(videos)
    transcripts = transcript_text(videos, enabled=settings.use_youtube_transcripts)
    news = latest_news(config["news"])
    analysis = generate_analysis(
        settings.gemini_api_key,
        report_type,
        market,
        news,
        digest,
        transcripts,
    )
    title = f"{config['title']} - {datetime.now().strftime('%d %b %Y')}"
    filename, path = create_pdf(title, analysis, config["category"])
    return store.save_report(config["category"], title, filename, path, summary=analysis[:600])


def send_latest_reports(report_type, store, settings):
    categories = [REPORT_CONFIG[report_type]["category"]] if report_type != "all" else [
        config["category"] for config in REPORT_CONFIG.values()
    ]
    recipients = store.list_subscribers()
    if settings.fallback_recipient and not recipients:
        recipients = [settings.fallback_recipient]

    results = []
    for category in categories:
        report = store.latest_report(category)
        if not report:
            results.append({"category": category, "status": "missing_report"})
            continue
        for recipient in recipients:
            ok, error = send_pdf(
                settings,
                recipient,
                report["title"],
                email_body(category),
                report["path"],
            )
            store.log_delivery(category, recipient, "SUCCESS" if ok else "FAILED", error)
            results.append({
                "category": category,
                "recipient": recipient,
                "status": "SUCCESS" if ok else "FAILED",
                "error": error,
            })
    return {"results": results}


def email_body(category):
    return f"""Dear Trader,

Please find attached your TradeZint {category} PDF analysis.

The report includes CE/PE leg format, expiry view, maximum profit, maximum risk, and trade management notes.

Risk disclosure: This is educational research only and not SEBI registered financial advice.

Regards,
TradeZint
"""
