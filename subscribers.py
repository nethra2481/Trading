import os
import re
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trading_app.db")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS delivery_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date TEXT NOT NULL,
                report_type TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                created_at TEXT NOT NULL
            )
            """
        )


def is_valid_email(email):
    return bool(email and EMAIL_RE.match(email.strip()))


def upsert_subscriber(email):
    if not is_valid_email(email):
        return False
    now = datetime.utcnow().isoformat()
    clean = email.strip().lower()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO subscribers(email, is_active, created_at, updated_at)
            VALUES (?, 1, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                is_active = 1,
                updated_at = excluded.updated_at
            """,
            (clean, now, now),
        )
    return True


def get_active_emails():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT email FROM subscribers WHERE is_active = 1 ORDER BY id ASC"
        ).fetchall()
    return [r["email"] for r in rows]


def log_delivery(run_date, report_type, email, subject, status, error_message=None):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO delivery_logs(run_date, report_type, email, subject, status, error_message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_date,
                report_type,
                email,
                subject,
                status,
                error_message,
                datetime.utcnow().isoformat(),
            ),
        )

