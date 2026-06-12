import os
import datetime
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)


def generate_report(prompt):
    """Call Gemini 2.5 Flash and return the response text."""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
        return (
            f"ANALYSIS STATUS:\n"
            f"AI analysis was unavailable at {ts} due to an API/network error.\n\n"
            "ACTION REQUIRED:\n"
            "1. Verify GEMINI_API_KEY is active and has quota.\n"
            "2. Check network/DNS on the server.\n"
            "3. The job will retry at the next scheduled interval."
        )


def normalize_report(raw_text, required_sections):
    """Force a stable, predictable section structure in the PDF output."""
    text = (raw_text or "").replace("\r\n", "\n").strip()
    if not text:
        text = "No analysis content generated."

    # Remove markdown artifacts
    text = re.sub(r'\*{1,2}', '', text)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)

    section_map = {sec: [] for sec in required_sections}
    current = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if current and section_map[current] and section_map[current][-1] != "":
                section_map[current].append("")
            continue

        normalized = re.sub(r"[:\-\s]+$", "", line.upper())
        matched = next((sec for sec in required_sections if normalized == sec), None)

        if matched:
            current = matched
        elif current:
            section_map[current].append(line)

    output = []
    for sec in required_sections:
        output.append(f"{sec}:")
        lines = section_map[sec]
        if not any(ln.strip() for ln in lines):
            output.append("  Analysis not available for this section.")
        else:
            output.extend(lines)
        output.append("")

    return "\n".join(output).strip()


# ─────────────────────────────────────────────
# REPORT 1: NIFTY INDEX OPTIONS (Weekly Expiry)
# Delivered at 9:00 AM IST
# ─────────────────────────────────────────────

def analyze_nifty(transcripts, news, market_data, gift_nifty, video_digest=""):
    required_sections = [
        "GLOBAL MARKET SUMMARY",
        "INDIA VIX & VOLATILITY ANALYSIS",
        "OVERALL VIEW FOR THE NEAREST WEEKLY EXPIRY",
        "TOP CE/PE OPTION STRATEGY (LEG FORMAT)",
        "MAXIMUM PROFIT AND RISK ASSOCIATED",
        "KEY LEVELS TO WATCH",
    ]

    # Format market data nicely
    mkt = "\n".join([f"  {k}: {v}" for k, v in market_data.items()])

    prompt = f"""
You are an expert NSE derivatives trader and quantitative analyst with 15+ years of experience.
Today is {datetime.datetime.now().strftime("%A, %d %B %Y")}. Data was captured at 8:00 AM IST.

=== GLOBAL MARKET DATA (8:00 AM IST) ===
{mkt}
Gift Nifty / SGX Nifty: {gift_nifty}

=== ALL AVAILABLE NEWS (Last 24 Hours) ===
{news}

=== TOP 5 YOUTUBE VIDEO DIGEST (Best Nifty Option Analysis Channels) ===
{video_digest}

=== VIDEO TRANSCRIPTS / DESCRIPTIONS ===
{transcripts}

=== TASK ===
Generate a comprehensive, professional daily Nifty Index OPTION TRADING analysis report for the NEAREST WEEKLY EXPIRY.
This will be emailed to a client at 9:00 AM IST in PDF format.

CRITICAL RULES:
- DO NOT use Markdown (no **, no #). Use PLAIN TEXT only.
- Use UPPERCASE for all section headings exactly as listed below.
- Be SPECIFIC: give exact strike prices, levels, premiums (estimated), lot sizes.
- Focus ONLY on OPTION TRADING (CE/PE), NOT equity buy/sell.
- Every strategy must be in LEG FORMAT with entry, target, stop-loss.
- State the nearest weekly expiry date explicitly.

REQUIRED SECTIONS (in this exact order, exact spelling):

GLOBAL MARKET SUMMARY
Analyze impact of Gift Nifty, Dow Jones Futures, Crude Oil, Dollar Index, and US 10-Year Bond Yield on today's Nifty opening and direction.

INDIA VIX & VOLATILITY ANALYSIS
Current India VIX level, what it means for option premiums, and whether to BUY or SELL options today.

OVERALL VIEW FOR THE NEAREST WEEKLY EXPIRY
State the expiry date. Give directional bias (Bullish/Bearish/Sideways). State key support, resistance, and pivot levels for Nifty.

TOP CE/PE OPTION STRATEGY (LEG FORMAT)
Give 2-3 concrete actionable strategies. For each:
  Strategy Name (e.g., Bull Call Spread, Long Straddle, etc.)
  Leg 1: BUY/SELL [Strike] [CE/PE] @ approx premium Rs. [X]
  Leg 2: BUY/SELL [Strike] [CE/PE] @ approx premium Rs. [X] (if applicable)
  Entry Time: [e.g., 9:20 AM - 9:45 AM]
  Target: [price/points]
  Stop Loss: [price/points]
  Rationale: [brief reason]

MAXIMUM PROFIT AND RISK ASSOCIATED
For each strategy above: Max Profit (Rs. per lot), Max Loss (Rs. per lot), Breakeven point(s), Risk:Reward ratio.

KEY LEVELS TO WATCH
Nifty call writing levels (resistance), put writing levels (support), max pain strike, and intraday pivot.
"""
    raw = generate_report(prompt)
    return normalize_report(raw, required_sections)


# ─────────────────────────────────────────────
# REPORT 2: FNO STOCK OPTIONS (Monthly Expiry)
# Delivered at 9:00 AM IST
# ─────────────────────────────────────────────

def analyze_fno(transcripts, news, market_data, gift_nifty, video_digest=""):
    required_sections = [
        "GLOBAL MARKET SUMMARY",
        "FNO MARKET OVERVIEW",
        "OVERALL VIEW FOR THE NEAREST MONTHLY EXPIRY",
        "TOP FNO STOCK CE/PE STRATEGY (LEG FORMAT)",
        "MAXIMUM PROFIT AND RISK ASSOCIATED",
        "FNO STOCKS TO WATCH",
    ]

    mkt = "\n".join([f"  {k}: {v}" for k, v in market_data.items()])

    prompt = f"""
You are an expert NSE F&O derivatives trader with 15+ years of experience trading FNO stocks.
Today is {datetime.datetime.now().strftime("%A, %d %B %Y")}. Data was captured at 8:00 AM IST.

=== GLOBAL MARKET DATA (8:00 AM IST) ===
{mkt}
Gift Nifty / SGX Nifty: {gift_nifty}

=== ALL AVAILABLE FNO NEWS (Last 24 Hours) ===
{news}

=== TOP 5 YOUTUBE VIDEO DIGEST (Best FNO Option Analysis Channels) ===
{video_digest}

=== VIDEO TRANSCRIPTS / DESCRIPTIONS ===
{transcripts}

=== TASK ===
Generate a comprehensive, professional daily FNO STOCK OPTION TRADING analysis for the NEAREST MONTHLY EXPIRY.
This will be emailed to a client at 9:00 AM IST in PDF format.

CRITICAL RULES:
- DO NOT use Markdown (no **, no #). Use PLAIN TEXT only.
- Use UPPERCASE for all section headings exactly as listed below.
- Be SPECIFIC: give exact stock names, strike prices, premiums (estimated), lot sizes.
- Focus ONLY on OPTION TRADING (CE/PE) on FNO stocks, NOT equity buy/sell.
- Every strategy must be in LEG FORMAT with entry, target, stop-loss.
- State the nearest monthly expiry date explicitly.

REQUIRED SECTIONS (in this exact order, exact spelling):

GLOBAL MARKET SUMMARY
Analyze impact of Gift Nifty, Dow Jones Futures, Crude Oil, Dollar Index, and US 10-Year Bond Yield on FNO stocks today.

FNO MARKET OVERVIEW
Overall F&O market sentiment: Bank Nifty direction, Fin Nifty, sector rotation. Any stocks added to or removed from F&O ban list.

OVERALL VIEW FOR THE NEAREST MONTHLY EXPIRY
State the expiry date. Give directional bias for top FNO stocks. Key sector themes for this expiry.

TOP FNO STOCK CE/PE STRATEGY (LEG FORMAT)
Give 3-4 concrete strategies on specific FNO stocks. For each:
  Stock: [Name] | Lot Size: [X] | CMP: approx [Y]
  Strategy: [e.g., Bull Call Spread]
  Leg 1: BUY/SELL [Strike] [CE/PE] @ approx premium Rs. [X]
  Leg 2: BUY/SELL [Strike] [CE/PE] @ approx premium Rs. [X] (if applicable)
  Entry: [time window]
  Target: [price/points]
  Stop Loss: [price/points]
  Rationale: [brief reason]

MAXIMUM PROFIT AND RISK ASSOCIATED
For each strategy: Max Profit (Rs. per lot), Max Loss (Rs. per lot), Breakeven, Risk:Reward ratio.

FNO STOCKS TO WATCH
Top 5 FNO stocks with high OI buildup, unusual options activity, or strong directional bias today.
"""
    raw = generate_report(prompt)
    return normalize_report(raw, required_sections)


# ─────────────────────────────────────────────
# REPORT 3: CNBC AWAAZ INTRADAY (Daily Scalping)
# Delivered at 9:30 AM IST
# ─────────────────────────────────────────────

def analyze_intraday(transcript, video_digest="", market_data=None, gift_nifty=None):
    required_sections = [
        "MORNING MARKET BRIEFING",
        "OVERALL VIEW FOR DAILY OPTION TRADING AND INTRADAY SCALPING",
        "INTRADAY OPTION STRATEGY (LEG FORMAT)",
        "SCALPING SETUPS",
        "MAXIMUM PROFIT AND RISK ASSOCIATED",
        "INTRADAY KEY LEVELS",
    ]

    mkt_str = ""
    if market_data:
        mkt_str = "\n".join([f"  {k}: {v}" for k, v in market_data.items()])
        mkt_str = f"\n=== LIVE MARKET DATA ===\n{mkt_str}\nGift Nifty: {gift_nifty}\n"

    prompt = f"""
You are an expert intraday option trader and CNBC Awaaz market analyst.
Today is {datetime.datetime.now().strftime("%A, %d %B %Y")}. Analysis is based on CNBC Awaaz morning live (7:00 AM - 9:00 AM IST).
{mkt_str}
=== CNBC AWAAZ MORNING LIVE CONTENT (7:00 AM - 9:00 AM IST) ===
{video_digest}

=== VIDEO TRANSCRIPTS / DESCRIPTIONS ===
{transcript}

=== TASK ===
Generate a comprehensive intraday OPTION TRADING and SCALPING analysis based on the CNBC Awaaz morning show.
This will be emailed to a client at 9:30 AM IST in PDF format.

CRITICAL RULES:
- DO NOT use Markdown (no **, no #). Use PLAIN TEXT only.
- Use UPPERCASE for all section headings exactly as listed below.
- Be SPECIFIC: give exact strikes, entry times, target, stop-loss for options.
- Focus on OPTION TRADING (CE/PE) for INTRADAY — positions to be squared off same day.
- Include both Nifty and Bank Nifty setups.

REQUIRED SECTIONS (in this exact order, exact spelling):

MORNING MARKET BRIEFING
Summarize what CNBC Awaaz experts said about the market opening. Key stocks they mentioned. Overall sentiment.

OVERALL VIEW FOR DAILY OPTION TRADING AND INTRADAY SCALPING
Today's intraday bias (Bullish/Bearish/Rangebound). Expected trading range for Nifty and Bank Nifty. Key catalysts for the day.

INTRADAY OPTION STRATEGY (LEG FORMAT)
Give 3 concrete intraday option strategies:
  Strategy Name
  Instrument: Nifty / Bank Nifty / Stock
  Leg 1: BUY/SELL [Strike] [CE/PE] @ approx premium Rs. [X]
  Leg 2: BUY/SELL [Strike] [CE/PE] @ approx premium Rs. [X] (if applicable)
  Entry Time: [e.g., 9:20 AM - 9:30 AM]
  Target: [premium/points]
  Stop Loss: [premium/points]
  Exit by: [time, e.g., 3:00 PM]

SCALPING SETUPS
2-3 quick scalping opportunities (15-30 minute trades) with exact entry/exit and option strikes.

MAXIMUM PROFIT AND RISK ASSOCIATED
For each strategy and scalp: Max Profit (Rs. per lot), Max Loss (Rs. per lot), Risk:Reward ratio.

INTRADAY KEY LEVELS
Nifty: Support 1, Support 2, Resistance 1, Resistance 2, Intraday Pivot
Bank Nifty: Support 1, Support 2, Resistance 1, Resistance 2, Intraday Pivot
"""
    raw = generate_report(prompt)
    return normalize_report(raw, required_sections)
