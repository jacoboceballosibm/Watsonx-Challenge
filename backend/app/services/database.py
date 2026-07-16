from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./prom.db")
SCHEMA_VERSION = 1


def _database_path() -> Path:
    if not DATABASE_URL.startswith("sqlite:///"):
        raise RuntimeError("Only sqlite:/// DATABASE_URL values are supported in this lightweight DB layer.")

    raw_path = DATABASE_URL.removeprefix("sqlite:///")
    path = Path(raw_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    db_path = _database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                professional_id TEXT NOT NULL UNIQUE,
                user_id TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
                professional_id TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS profiles (
                professional_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                w3_link TEXT,
                availability_date TEXT NOT NULL,
                current_open_seats_json TEXT NOT NULL DEFAULT '[]',
                skills_json TEXT NOT NULL DEFAULT '[]',
                band TEXT,
                location TEXT,
                cv_repository_url TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS seats (
                seat_id TEXT PRIMARY KEY,
                owner_professional_id TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS cvs (
                cv_id TEXT PRIMARY KEY,
                professional_id TEXT NOT NULL,
                name TEXT NOT NULL,
                target_role TEXT,
                source_type TEXT NOT NULL DEFAULT 'manual',
                tags_json TEXT NOT NULL DEFAULT '[]',
                cv_contact_json TEXT NOT NULL DEFAULT '{}',
                cv_overview TEXT,
                skills_json TEXT NOT NULL DEFAULT '[]',
                cv_sections_json TEXT NOT NULL DEFAULT '{}',
                is_default INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (professional_id) REFERENCES profiles(professional_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS cv_agent_runs (
                run_id TEXT PRIMARY KEY,
                cv_id TEXT,
                professional_id TEXT NOT NULL,
                role_description TEXT,
                source_cv_text TEXT,
                tailored_cv_text TEXT NOT NULL,
                changes_json TEXT NOT NULL DEFAULT '[]',
                warnings_json TEXT NOT NULL DEFAULT '[]',
                model TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cv_id) REFERENCES cvs(cv_id) ON DELETE SET NULL,
                FOREIGN KEY (professional_id) REFERENCES profiles(professional_id) ON DELETE CASCADE
            );
            """
        )
        _ensure_column(conn, "profiles", "cv_overview", "TEXT")
        _ensure_column(conn, "profiles", "cv_contact_json", "TEXT NOT NULL DEFAULT '{}'")
        _ensure_column(conn, "profiles", "cv_sections_json", "TEXT NOT NULL DEFAULT '{}'")
        conn.execute(
            "INSERT OR IGNORE INTO schema_migrations (version) VALUES (?)",
            (SCHEMA_VERSION,),
        )


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
