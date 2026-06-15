import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_secret_key: str
    database_path: str
    timezone: str
    gemini_api_key: str
    youtube_api_key: str
    use_youtube_transcripts: bool
    email_address: str
    email_app_password: str
    fallback_recipient: str

    def integration_status(self):
        return {
            "database": bool(self.database_path),
            "gemini": bool(self.gemini_api_key),
            "youtube": bool(self.youtube_api_key),
            "email": bool(self.email_address and self.email_app_password),
            "market_data": True,
            "news": True,
        }


def get_settings():
    return Settings(
        app_secret_key=os.getenv("APP_SECRET_KEY", "dev-secret"),
        database_path=os.getenv("DATABASE_PATH", "tradezint.sqlite3"),
        timezone="Asia/Kolkata",
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        youtube_api_key=os.getenv("YOUTUBE_API_KEY", ""),
        use_youtube_transcripts=os.getenv("USE_YT_TRANSCRIPTS", "false").lower() in {"1", "true", "yes"},
        email_address=os.getenv("EMAIL_ADDRESS", ""),
        email_app_password=os.getenv("EMAIL_APP_PASSWORD", ""),
        fallback_recipient=os.getenv("REPORT_RECIPIENT_FALLBACK", ""),
    )
