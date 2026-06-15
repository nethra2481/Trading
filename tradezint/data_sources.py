from datetime import datetime, timedelta, timezone

import requests
import yfinance as yf
from bs4 import BeautifulSoup
from gnews import GNews
from googleapiclient.discovery import build


def get_market_snapshot():
    tickers = {
        "Dow Jones Futures": "YM=F",
        "Crude Oil WTI": "CL=F",
        "Dollar Index": "DX-Y.NYB",
        "US 10-Year Bond Yield": "^TNX",
        "India VIX": "^INDIAVIX",
    }
    data = {}
    for label, ticker in tickers.items():
        try:
            history = yf.Ticker(ticker).history(period="1d")
            data[label] = round(float(history["Close"].iloc[-1]), 2) if not history.empty else "N/A"
        except Exception as exc:
            data[label] = f"Unavailable: {exc}"
    data["Gift Nifty"] = get_gift_nifty()
    data["Captured At"] = datetime.now().strftime("%Y-%m-%d %H:%M IST")
    return data


def get_gift_nifty():
    try:
        response = requests.get(
            "https://www.google.com/search?q=gift+nifty+live",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8,
        )
        text = BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True)
        for token in text.split():
            value = token.replace(",", "")
            if value.replace(".", "", 1).isdigit():
                number = float(value)
                if 10000 <= number <= 40000:
                    return number
    except Exception:
        pass
    return "N/A"


def youtube_search(api_key, query, max_results=5, days_back=2):
    if not api_key:
        return []
    published_after = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat().replace("+00:00", "Z")
    youtube = build("youtube", "v3", developerKey=api_key)
    response = youtube.search().list(
        part="snippet",
        q=query,
        maxResults=max_results,
        type="video",
        order="relevance",
        publishedAfter=published_after,
    ).execute()
    videos = []
    for item in response.get("items", []):
        snippet = item.get("snippet", {})
        video_id = item.get("id", {}).get("videoId")
        if video_id:
            videos.append({
                "id": video_id,
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "description": snippet.get("description", ""),
                "published_at": snippet.get("publishedAt", ""),
                "url": f"https://www.youtube.com/watch?v={video_id}",
            })
    return videos


def video_digest(videos):
    if not videos:
        return "No YouTube videos found."
    return "\n".join(
        f"{idx}. {video['channel']} - {video['title']} ({video['url']})"
        for idx, video in enumerate(videos[:5], 1)
    )


def transcript_text(videos, enabled=False):
    if enabled:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
        except Exception:
            enabled = False

    chunks = []
    for video in videos:
        if not enabled:
            chunks.append(f"{video['title']}: {video.get('description') or 'No description available.'}")
            continue
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video["id"], languages=["hi", "en"])
            chunks.append(" ".join(item["text"] for item in transcript))
        except Exception:
            chunks.append(f"{video['title']}: {video.get('description') or 'Transcript unavailable.'}")
    return "\n\n".join(chunks)


def latest_news(query, max_results=15):
    try:
        client = GNews(max_results=max_results, period="1d")
        articles = client.get_news(query)
        return "\n".join(
            f"- {item.get('title', '').strip()}"
            for item in articles
            if item.get("title")
        ) or "No major news found."
    except Exception as exc:
        return f"News unavailable: {exc}"
