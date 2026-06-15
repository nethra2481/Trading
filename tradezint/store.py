import os
import re
import sqlite3
from datetime import datetime

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class Store:
    def __init__(self, database_path):
        self.database_path = database_path

    def connect(self):
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS subscribers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    path TEXT NOT NULL,
                    summary TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS delivery_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_type TEXT NOT NULL,
                    email TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )

    def add_subscriber(self, email):
        if not email or not EMAIL_RE.match(email):
            return False
        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO subscribers(email, active, created_at, updated_at)
                VALUES (?, 1, ?, ?)
                ON CONFLICT(email) DO UPDATE SET active = 1, updated_at = excluded.updated_at
                """,
                (email, now, now),
            )
        return True

    def list_subscribers(self):
        with self.connect() as conn:
            rows = conn.execute("SELECT email FROM subscribers WHERE active = 1 ORDER BY id").fetchall()
        return [row["email"] for row in rows]

    def save_report(self, category, title, filename, path, summary=""):
        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO reports(category, title, filename, path, summary, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (category, title, filename, path, summary, now),
            )
        return self.get_report(cur.lastrowid)

    def list_reports(self, category=None):
        sql = "SELECT * FROM reports"
        params = []
        if category:
            sql += " WHERE category = ?"
            params.append(category)
        sql += " ORDER BY created_at DESC"
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def get_report(self, report_id):
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        if not row:
            return None
        report = dict(row)
        if not os.path.exists(report["path"]):
            return None
        return report

    def latest_report(self, category):
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM reports WHERE category = ? ORDER BY created_at DESC LIMIT 1",
                (category,),
            ).fetchone()
        return dict(row) if row else None

    def log_delivery(self, report_type, email, status, error_message=None):
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO delivery_logs(report_type, email, status, error_message, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (report_type, email, status, error_message, datetime.utcnow().isoformat()),
            )

    def list_delivery_logs(self, limit=10):
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM delivery_logs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
