import os
import time
import logging
from datetime import datetime, timedelta, timezone
import yfinance as yf
from gnews import GNews
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
USE_YT_TRANSCRIPTS = os.getenv("USE_YT_TRANSCRIPTS", "0").strip().lower() in {"1", "true", "yes"}

logging.getLogger("yfinance").setLevel(logging.ERROR)

# ─────────────────────────────────────────────
# YOUTUBE
# ─────────────────────────────────────────────

def get_top_youtube_videos(query, max_results=5, days_back=2):
    """Search YouTube for the most relevant recent videos for a query."""
    try:
        if not YOUTUBE_API_KEY:
            print("YOUTUBE_API_KEY missing; cannot fetch YouTube videos.")
            return []

        published_after = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat().replace("+00:00", "Z")
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(
            part="snippet",
            maxResults=max_results,
            q=query,
            type="video",
            order="relevance",
            publishedAfter=published_after
        )
        response = request.execute()
        videos = []
        for item in response.get('items', []):
            video_id = item.get('id', {}).get('videoId')
            snippet = item.get('snippet', {})
            if not video_id:
                continue
            videos.append({
                "id": video_id,
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "description": snippet.get("description", ""),
                "published_at": snippet.get("publishedAt", "")
            })
        return videos
    except Exception as e:
        print(f"Error fetching YouTube videos for '{query}': {e}")
        return []


def get_cnbc_awaaz_morning_video():
    """Specifically target CNBC Awaaz morning live stream for today."""
    try:
        if not YOUTUBE_API_KEY:
            return []

        # Search for CNBC Awaaz morning Pehla Sauda live stream from last 1 day
        published_after = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat().replace("+00:00", "Z")
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

        # Try multiple queries to find the morning live stream
        queries = [
            "CNBC Awaaz Pehla Sauda Live Today Morning",
            "CNBC Awaaz Morning Live Market Open Today",
            "CNBC Awaaz 9 baje se pehle intraday trading"
        ]

        videos = []
        for query in queries:
            request = youtube.search().list(
                part="snippet",
                maxResults=3,
                q=query,
                type="video",
                order="date",
                publishedAfter=published_after
            )
            response = request.execute()
            for item in response.get('items', []):
                video_id = item.get('id', {}).get('videoId')
                snippet = item.get('snippet', {})
                channel = snippet.get("channelTitle", "")
                title = snippet.get("title", "")
                if not video_id:
                    continue
                # Prefer actual CNBC Awaaz channel
                if "CNBC" in channel or "cnbc" in channel.lower() or "Awaaz" in channel:
                    videos.insert(0, {
                        "id": video_id,
                        "title": title,
                        "channel": channel,
                        "description": snippet.get("description", ""),
                        "published_at": snippet.get("publishedAt", "")
                    })
                else:
                    videos.append({
                        "id": video_id,
                        "title": title,
                        "channel": channel,
                        "description": snippet.get("description", ""),
                        "published_at": snippet.get("publishedAt", "")
                    })
            if videos:
                break  # Found results, stop trying other queries

        return videos[:3]
    except Exception as e:
        print(f"Error fetching CNBC Awaaz videos: {e}")
        return []


def get_video_transcripts(videos):
    """Extract and combine transcripts from a list of videos with fallbacks."""
    combined_transcript = ""
    transcript_rate_limited = False
    for entry in videos:
        if isinstance(entry, dict):
            vid = entry.get("id")
            title = entry.get("title", "")
            channel = entry.get("channel", "")
            desc = entry.get("description", "")
        else:
            vid = entry
            title = ""
            channel = ""
            desc = ""
        if not vid:
            continue

        if not USE_YT_TRANSCRIPTS:
            fallback_text = (desc[:1500] if desc else "No description available.")
            combined_transcript += (
                f"\n--- Video: {title} | Channel: {channel} (Metadata Mode) ---\n"
                f"Description: {fallback_text}\n"
            )
            continue

        if not transcript_rate_limited:
            try:
                transcript = YouTubeTranscriptApi.get_transcript(vid, languages=['hi', 'en'])
                text = " ".join([t['text'] for t in transcript])
                combined_transcript += f"\n--- Video: {title} | Channel: {channel} ---\n{text}\n"
            except Exception as e:
                err = str(e)
                if "Too Many Requests" in err or "429" in err:
                    transcript_rate_limited = True
                    print("YouTube transcript API rate-limited. Falling back to metadata.")
                else:
                    print(f"Transcript unavailable for {vid}. Using metadata fallback.")
                fallback_text = (desc[:1500] if desc else "No description available.")
                combined_transcript += (
                    f"\n--- Video: {title} | Channel: {channel} (Metadata Fallback) ---\n"
                    f"Description: {fallback_text}\n"
                )
            time.sleep(1.2)
        else:
            fallback_text = (desc[:1500] if desc else "No description available.")
            combined_transcript += (
                f"\n--- Video: {title} | Channel: {channel} (Rate-Limited Fallback) ---\n"
                f"Description: {fallback_text}\n"
            )
    return combined_transcript


# ─────────────────────────────────────────────
# MARKET DATA
# ─────────────────────────────────────────────

def get_market_data():
    """Fetch global market data at the current time (called at 8:00 AM IST)."""
    data = {}
    tickers = {
        'Dow Jones Futures': 'YM=F',
        'Crude Oil (WTI)': 'CL=F',
        'Dollar Index (DXY)': 'DX-Y.NYB',
        'US 10-Year Bond Yield': '^TNX',
        'India VIX': '^INDIAVIX',
        'SGX Nifty / Gift Nifty Proxy': '^NSEI',
    }
    for name, ticker in tickers.items():
        try:
            ticker_obj = yf.Ticker(ticker)
            history = ticker_obj.history(period="1d")
            if not history.empty:
                val = round(float(history['Close'].iloc[-1]), 2)
                data[name] = val
            else:
                data[name] = "N/A"
        except Exception as e:
            print(f"Error fetching {name} ({ticker}): {e}")
            data[name] = "Error"
    return data


def get_gift_nifty():
    """Fetch Gift Nifty points — uses best-effort scrape then NSEI fallback."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        url = "https://www.google.com/search?q=gift+nifty+live+price+today"
        response = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        for token in text.split():
            cleaned = token.replace(",", "")
            if cleaned.replace(".", "", 1).isdigit():
                val = float(cleaned)
                if 10000 <= val <= 50000:
                    return f"{val} (scraped)"
    except Exception:
        pass

    try:
        history = yf.Ticker("^NSEI").history(period="1d")
        if not history.empty:
            value = round(float(history["Close"].iloc[-1]), 2)
            return f"{value} (Nifty 50 proxy)"
    except Exception:
        pass

    return "N/A"


# ─────────────────────────────────────────────
# NEWS
# ─────────────────────────────────────────────

def get_news(query, max_results=20):
    """Fetch recent news articles for a query from the last 24 hours."""
    try:
        google_news = GNews(max_results=max_results, period="1d")
        json_resp = google_news.get_news(query)
        seen = set()
        lines = []
        for article in json_resp:
            title = article.get("title", "").strip()
            publisher = article.get("publisher", {}).get("title", "")
            if not title or title in seen:
                continue
            seen.add(title)
            pub_str = f" [{publisher}]" if publisher else ""
            lines.append(f"- {title}{pub_str}")
        return "\n".join(lines) if lines else "No major news found."
    except Exception as e:
        print(f"Error fetching news for '{query}': {e}")
        return "No news found."


def get_all_nifty_news():
    """Aggregate news from multiple Nifty option-relevant queries."""
    queries = [
        "Nifty 50 option trading analysis today",
        "Nifty weekly expiry CE PE option",
        "India stock market open today Nifty",
        "NSE Nifty options strategy",
    ]
    all_lines = set()
    for q in queries:
        news = get_news(q, max_results=10)
        for line in news.splitlines():
            if line.strip():
                all_lines.add(line.strip())
    return "\n".join(sorted(all_lines)) if all_lines else "No news found."


def get_all_fno_news():
    """Aggregate news from multiple FNO-relevant queries."""
    queries = [
        "FNO stock option trading analysis today",
        "NSE FNO stocks monthly expiry CE PE",
        "Indian stock futures options news today",
        "F&O ban list NSE today",
    ]
    all_lines = set()
    for q in queries:
        news = get_news(q, max_results=10)
        for line in news.splitlines():
            if line.strip():
                all_lines.add(line.strip())
    return "\n".join(sorted(all_lines)) if all_lines else "No news found."


if __name__ == "__main__":
    print("Testing Data Ingestion...")
    print("Market Data:", get_market_data())
    print("Gift Nifty:", get_gift_nifty())
    print("Nifty News:", get_all_nifty_news())
