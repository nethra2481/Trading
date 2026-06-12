import os
import datetime
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Initialize the GenAI client
client = genai.Client(api_key=GEMINI_API_KEY)

def generate_report(prompt):
    """Helper function to call Gemini and return the response."""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return (
            "ANALYSIS STATUS:\n"
            f"Automated AI analysis was unavailable at {ts} due to API/network error.\n\n"
            "ACTION REQUIRED:\n"
            "1. Check internet/DNS access on the machine.\n"
            "2. Verify GEMINI_API_KEY is active and has quota.\n"
            "3. Re-run the job once connectivity is restored.\n\n"
            "DATA QUALITY NOTE:\n"
            "Report generated in fallback mode because AI analysis service was unreachable."
        )

def normalize_report(raw_text, required_sections):
    """Force stable report structure and section order."""
    text = (raw_text or "").replace("\r\n", "\n").strip()
    if not text:
        text = "No analysis content generated."

    # Normalize lightweight markdown artifacts.
    text = text.replace("**", "")

    section_map = {sec: [] for sec in required_sections}
    current = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if current and section_map[current] and section_map[current][-1] != "":
                section_map[current].append("")
            continue

        normalized = re.sub(r"[:\-\s]+$", "", line.upper())
        matched = None
        for sec in required_sections:
            if normalized == sec:
                matched = sec
                break

        if matched:
            current = matched
            continue

        if current:
            section_map[current].append(line)

    output = []
    for sec in required_sections:
        output.append(f"{sec}:")
        lines = [ln for ln in section_map[sec]]
        if not any(ln.strip() for ln in lines):
            output.append("No clear output from model for this section; review required.")
        else:
            output.extend(lines)
        output.append("")

    return "\n".join(output).strip()

def analyze_nifty(transcripts, news, market_data, gift_nifty, video_digest=""):
    required_sections = [
        "GLOBAL MARKET SUMMARY",
        "OVERALL VIEW FOR THE NEAREST WEEKLY EXPIRY",
        "BEST BUY/SELL STRATEGY FOR CE/PE (LEG FORMAT)",
        "MAXIMUM PROFIT AND RISK ASSOCIATED",
    ]
    prompt = f"""
    You are an expert quantitative trader and financial analyst.
    I need a daily analysis for Nifty Index option trading based on the following data gathered at 8:00 AM IST.

    Market Data (Dow Jones Futures, Crude Oil Price, Dollar Index, US 10 year Bond Yield):
    {market_data}
    Gift Nifty points: {gift_nifty}

    Latest News:
    {news}

    Top 5 Video Digest:
    {video_digest}

    Transcripts from top 5 YouTube videos analyzing Nifty Options today:
    {transcripts}

    Based on all this information, generate a highly professional, direct daily trading analysis report.
    DO NOT use Markdown formatting (no asterisks **, no hashes #). Use UPPERCASE for section headers.
    Avoid vague wording. Use specific levels and clear action points.

    The report MUST include these sections in this exact order and exact spelling:
    GLOBAL MARKET SUMMARY
    Summarize impact of Gift Nifty, Dow Jones, Crude Oil, Dollar Index, and Bond Yields.

    OVERALL VIEW FOR THE NEAREST WEEKLY EXPIRY
    Directional bias and key levels (support, resistance, pivot).

    BEST BUY/SELL STRATEGY FOR CE/PE (LEG FORMAT)
    Provide exact option legs for actionable CE/PE setup.

    MAXIMUM PROFIT AND RISK ASSOCIATED
    State max profit, max risk, breakeven points, and risk-reward.
    """
    raw = generate_report(prompt)
    return normalize_report(raw, required_sections)

def analyze_fno(transcripts, news, market_data, gift_nifty, video_digest=""):
    required_sections = [
        "GLOBAL MARKET SUMMARY",
        "OVERALL VIEW FOR THE NEAREST MONTHLY EXPIRY",
        "BEST BUY/SELL STRATEGY FOR CE/PE (LEG FORMAT)",
        "MAXIMUM PROFIT AND RISK ASSOCIATED",
    ]
    prompt = f"""
    You are an expert quantitative trader and financial analyst.
    I need a daily analysis for FNO stock option trading based on the following data gathered at 8:00 AM IST.

    Market Data (Dow Jones Futures, Crude Oil Price, Dollar Index, US 10 year Bond Yield):
    {market_data}
    Gift Nifty points: {gift_nifty}

    Latest News:
    {news}

    Top 5 Video Digest:
    {video_digest}

    Transcripts from top 5 YouTube videos analyzing FNO stock options today:
    {transcripts}

    Based on all this information, generate a highly professional, direct daily trading analysis report.
    DO NOT use Markdown formatting (no asterisks **, no hashes #). Use UPPERCASE for section headers.
    Avoid vague wording. Use specific levels and clear action points.

    The report MUST include these sections in this exact order and exact spelling:
    GLOBAL MARKET SUMMARY
    Briefly summarize the impact of Gift Nifty, Dow Jones, Crude Oil, Dollar Index, and Bond Yields.

    OVERALL VIEW FOR THE NEAREST MONTHLY EXPIRY
    Provide the directional bias and key levels for FNO stocks.

    BEST BUY/SELL STRATEGY FOR CE/PE (LEG FORMAT)
    Provide exact option legs for actionable CE/PE setup in FNO stocks.

    MAXIMUM PROFIT AND RISK ASSOCIATED
    Clearly state max profit, max risk, breakeven points, and risk-reward.
    """
    raw = generate_report(prompt)
    return normalize_report(raw, required_sections)

def analyze_intraday(transcript, video_digest=""):
    required_sections = [
        "OVERALL VIEW FOR DAILY TRADING AND INTRADAY SCALPING",
        "BEST BUY/SELL STRATEGY FOR CE/PE (LEG FORMAT)",
        "MAXIMUM PROFIT AND RISK ASSOCIATED",
    ]
    prompt = f"""
    You are an expert quantitative trader and financial analyst.
    I need a daily analysis based on the morning CNBC Awaaz live stream from 7:00 AM to 9:00 AM.

    Transcript / Highlights from the stream:
    {transcript}

    Live Video Digest:
    {video_digest}

    Based on this, generate a highly professional, direct daily trading analysis report.
    DO NOT use Markdown formatting (no asterisks **, no hashes #). Use UPPERCASE for section headers.
    Avoid vague wording. Use specific levels and clear action points.

    The report MUST include these sections in this exact order and exact spelling:
    OVERALL VIEW FOR DAILY TRADING AND INTRADAY SCALPING
    Summarize the general market sentiment and key actionable levels for intraday.

    BEST BUY/SELL STRATEGY FOR CE/PE (LEG FORMAT)
    Provide exact option legs for actionable CE/PE setup.

    MAXIMUM PROFIT AND RISK ASSOCIATED
    Clearly state max profit, max risk, breakeven points, and risk-reward.
    """
    raw = generate_report(prompt)
    return normalize_report(raw, required_sections)
