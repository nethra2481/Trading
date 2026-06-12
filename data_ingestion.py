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

# Reduce noisy upstream logs from yfinance/yahoo internals.
logging.getLogger("yfinance").setLevel(logging.ERROR)

def get_top_youtube_videos(query, max_results=5):
    """Search YouTube for the most relevant recent videos for a query."""
    try:
        if not YOUTUBE_API_KEY:
            print("YOUTUBE_API_KEY missing; cannot fetch YouTube videos.")
            return []

        published_after = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat().replace("+00:00", "Z")
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
                "description": snippet.get("description", ""),
                "published_at": snippet.get("publishedAt", "")
            })
        return videos
    except Exception as e:
        print(f"Error fetching YouTube videos for '{query}': {e}")
        return []

def get_video_transcripts(videos):
    """Extract and combine transcripts from a list of videos/IDs with fallbacks."""
    combined_transcript = ""
    transcript_rate_limited = False
    for entry in videos:
        if isinstance(entry, dict):
            vid = entry.get("id")
            title = entry.get("title", "")
            desc = entry.get("description", "")
        else:
            vid = entry
            title = ""
            desc = ""
        if not vid:
            continue
        if not USE_YT_TRANSCRIPTS:
            fallback_text = (desc[:1200] if desc else "No description available.")
            combined_transcript += (
                f"\n--- Video {vid}: {title} (Metadata Mode) ---\n"
                f"Description: {fallback_text}\n"
            )
            continue
        if not transcript_rate_limited:
            try:
                transcript = YouTubeTranscriptApi.get_transcript(vid, languages=['en', 'hi'])
                text = " ".join([t['text'] for t in transcript])
                combined_transcript += f"\n--- Video {vid}: {title} ---\n{text}\n"
            except Exception as e:
                err = str(e)
                if "Too Many Requests" in err or "429" in err:
                    transcript_rate_limited = True
                    print("YouTube transcript API rate-limited (429). Falling back to video metadata for remaining videos.")
                else:
                    print(f"Transcript unavailable for {vid}. Using metadata fallback.")
                fallback_text = (desc[:1200] if desc else "No description available.")
                combined_transcript += (
                    f"\n--- Video {vid}: {title} (Fallback Metadata) ---\n"
                    f"Transcript unavailable. Using title/description context.\n"
                    f"Description: {fallback_text}\n"
                )
            time.sleep(1.2)
        else:
            fallback_text = (desc[:1200] if desc else "No description available.")
            combined_transcript += (
                f"\n--- Video {vid}: {title} (Fallback Metadata) ---\n"
                f"Transcript skipped due to earlier rate limit.\n"
                f"Description: {fallback_text}\n"
            )
    return combined_transcript

def get_market_data():
    """Fetch global market data using yfinance at the current time."""
    data = {}
    tickers = {
        'Dow Jones Futures': 'YM=F',
        'Crude Oil': 'CL=F',
        'Dollar Index': 'DX-Y.NYB',
        'US 10-Yr Bond Yield': '^TNX'
    }
    for name, ticker in tickers.items():
        try:
            ticker_obj = yf.Ticker(ticker)
            # Get the latest price
            history = ticker_obj.history(period="1d")
            if not history.empty:
                data[name] = history['Close'].iloc[-1]
            else:
                data[name] = "N/A"
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            data[name] = "Error"
    return data

def get_gift_nifty():
    """Fetch Gift Nifty points with best-effort fallbacks."""
    try:
        # Yahoo doesn't reliably provide Gift Nifty in this setup.
        # Use NIFTY 50 spot as a stable fallback proxy.
        history = yf.Ticker("^NSEI").history(period="1d")
        if not history.empty:
            value = float(history["Close"].iloc[-1])
            return f"{value} (NIFTY 50 spot fallback)"

        # 2) Fallback scrape (best effort only).
        headers = {"User-Agent": "Mozilla/5.0"}
        url = "https://www.google.com/search?q=gift+nifty+live+price"
        response = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        for token in text.split():
            cleaned = token.replace(",", "")
            if cleaned.replace(".", "", 1).isdigit():
                val = float(cleaned)
                if 10000 <= val <= 50000:
                    return val
        return "N/A"
    except Exception as e:
        print(f"Error fetching Gift Nifty: {e}")
        return "N/A"

def get_news(query, max_results=5):
    """Fetch recent news articles based on a query."""
    try:
        google_news = GNews(max_results=max_results, period="1d")
        json_resp = google_news.get_news(query)
        seen = set()
        lines = []
        for article in json_resp:
            title = article.get("title", "").strip()
            if not title or title in seen:
                continue
            seen.add(title)
            lines.append(f"- {title}")
        return "\n".join(lines) if lines else "No major news found."
    except Exception as e:
        print(f"Error fetching news for {query}: {e}")
        return "No news found."

if __name__ == "__main__":
    # Test
    print("Testing Data Ingestion...")
    print(get_market_data())
    print(get_news("Nifty 50"))
