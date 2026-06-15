from datetime import datetime

from google import genai


SECTION_MAP = {
    "nifty": [
        "GLOBAL MARKET SUMMARY",
        "INDIA VIX AND VOLATILITY VIEW",
        "OVERALL VIEW FOR NEAREST WEEKLY EXPIRY",
        "BEST CE/PE OPTION STRATEGIES IN LEG FORMAT",
        "MAXIMUM PROFIT AND RISK ASSOCIATED",
        "KEY LEVELS AND TRADE MANAGEMENT",
        "RISK DISCLOSURE",
    ],
    "fno": [
        "GLOBAL MARKET SUMMARY",
        "FNO MARKET OVERVIEW",
        "OVERALL VIEW FOR NEAREST MONTHLY EXPIRY",
        "BEST FNO CE/PE STRATEGIES IN LEG FORMAT",
        "MAXIMUM PROFIT AND RISK ASSOCIATED",
        "FNO STOCKS TO WATCH",
        "RISK DISCLOSURE",
    ],
    "intraday": [
        "CNBC AWAAZ MORNING BRIEFING",
        "OVERALL VIEW FOR DAILY OPTION TRADING",
        "INTRADAY OPTION STRATEGIES IN LEG FORMAT",
        "SCALPING SETUPS",
        "MAXIMUM PROFIT AND RISK ASSOCIATED",
        "INTRADAY KEY LEVELS",
        "RISK DISCLOSURE",
    ],
}


def build_prompt(report_type, market_snapshot, news, videos, transcripts):
    sections = "\n".join(SECTION_MAP[report_type])
    expiry = "nearest weekly expiry" if report_type == "nifty" else "nearest monthly expiry"
    if report_type == "intraday":
        expiry = "same-day intraday and scalping"
    return f"""
You are an experienced NSE options analyst. Generate a plain-text PDF-ready report.
Today: {datetime.now().strftime("%A, %d %B %Y")}
Report type: {report_type.upper()}
Expiry focus: {expiry}

Market snapshot captured at 8:00 AM IST:
{market_snapshot}

Recent news:
{news}

Top YouTube source digest:
{videos}

Video transcript or description text:
{transcripts}

Rules:
- Use plain text only.
- Use the exact section headings below.
- Give CE/PE option strategies in leg format.
- Include BUY/SELL, strike, CE/PE, estimated premium, entry window, target, stop loss, and rationale.
- Include maximum profit, maximum loss, breakeven, and risk-reward wherever possible.
- Make uncertainty explicit. Do not pretend unavailable data is known.
- Add a short risk disclosure.

Required headings:
{sections}
"""


def generate_analysis(api_key, report_type, market_snapshot, news, videos, transcripts):
    if not api_key:
        return unavailable_report(report_type, "GEMINI_API_KEY is not configured.")
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=build_prompt(report_type, market_snapshot, news, videos, transcripts),
        )
        return normalize_sections(response.text or "", SECTION_MAP[report_type])
    except Exception as exc:
        return unavailable_report(report_type, f"Gemini generation failed: {exc}")


def normalize_sections(text, required_sections):
    cleaned = (text or "").replace("**", "").replace("#", "").strip()
    if not cleaned:
        cleaned = "No analysis content generated."
    missing = [section for section in required_sections if section not in cleaned.upper()]
    if not missing:
        return cleaned
    appended = [cleaned, ""]
    for section in missing:
        appended.append(f"{section}:")
        appended.append("Analysis not available for this section.")
        appended.append("")
    return "\n".join(appended).strip()


def unavailable_report(report_type, reason):
    sections = []
    for section in SECTION_MAP[report_type]:
        sections.append(f"{section}:")
        if section == "RISK DISCLOSURE":
            sections.append("This report is educational only and is not SEBI registered financial advice.")
        else:
            sections.append(f"Analysis unavailable. {reason}")
        sections.append("")
    return "\n".join(sections).strip()
