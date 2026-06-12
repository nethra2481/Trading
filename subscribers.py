import os
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def get_conn():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set. Please ensure Neon DB is configured.")
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS subscribers (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS delivery_logs (
                    id SERIAL PRIMARY KEY,
                    run_date VARCHAR(50) NOT NULL,
                    report_type VARCHAR(50) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    subject VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS reports (
                    id SERIAL PRIMARY KEY,
                    category VARCHAR(50) NOT NULL,
                    date_str VARCHAR(50) NOT NULL,
                    filename VARCHAR(255) NOT NULL UNIQUE,
                    pdf_bytes BYTEA NOT NULL,
                    created_at TIMESTAMP NOT NULL
                )
                """
            )
        conn.commit()


def is_valid_email(email):
    return bool(email and EMAIL_RE.match(email.strip()))


def upsert_subscriber(email):
    if not is_valid_email(email):
        return False
    now = datetime.utcnow()
    clean = email.strip().lower()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO subscribers(email, is_active, created_at, updated_at)
                VALUES (%s, 1, %s, %s)
                ON CONFLICT (email) DO UPDATE SET
                    is_active = 1,
                    updated_at = EXCLUDED.updated_at
                """,
                (clean, now, now),
            )
        conn.commit()
    return True


def get_active_emails():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT email FROM subscribers WHERE is_active = 1 ORDER BY id ASC")
            rows = cur.fetchall()
    return [r["email"] for r in rows]


def log_delivery(run_date, report_type, email, subject, status, error_message=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO delivery_logs(run_date, report_type, email, subject, status, error_message, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    run_date,
                    report_type,
                    email,
                    subject,
                    status,
                    error_message,
                    datetime.utcnow(),
                ),
            )
        conn.commit()


def save_report(category, date_str, filename, pdf_bytes):
    """Saves a generated PDF to the database."""
    now = datetime.utcnow()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO reports(category, date_str, filename, pdf_bytes, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (filename) DO UPDATE SET
                    pdf_bytes = EXCLUDED.pdf_bytes,
                    created_at = EXCLUDED.created_at
                """,
                (category, date_str, filename, psycopg2.Binary(pdf_bytes), now),
            )
        conn.commit()


def get_all_reports_metadata():
    """Returns metadata for all generated reports, newest first."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT filename, category, date_str, created_at FROM reports ORDER BY created_at DESC"
            )
            rows = cur.fetchall()
            
    # Convert created_at to timestamp float to match existing UI expectations
    return [
        {
            'filename': r['filename'],
            'category': r['category'],
            'date_str': r['date_str'],
            'mtime': r['created_at'].timestamp()
        }
        for r in rows
    ]


def get_report_bytes(filename):
    """Returns the raw PDF bytes for a given filename."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pdf_bytes FROM reports WHERE filename = %s", (filename,))
            row = cur.fetchone()
            if row:
                return bytes(row['pdf_bytes'])
            return None
