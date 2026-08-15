"""SQLite connection and query helpers for the IOSA refinery database.

Provides three things: a connection factory, a one-time schema init
function, and a safe read-only query runner for the SQL tool node.
"""
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

from src.iosa.logger import setup_logger

load_dotenv()

logger = setup_logger(__name__)

DB_PATH = os.getenv("DB_PATH", "data/refinery.db")
SCHEMA_PATH = Path("src/iosa/database/schema.sql")


def get_connection() -> sqlite3.Connection:
    """Open a connection to the SQLite database.

    row_factory = sqlite3.Row makes rows behave like dicts,
    so code can do row["tag"] instead of row[0].
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables from schema.sql if they don't already exist.

    Safe to call multiple times, CREATE TABLE without IF NOT EXISTS
    will fail on second run, so we check for the equipment table first.
    """
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='equipment'"
    )
    if cursor.fetchone() is not None:
        logger.info("init_db: tables already exist, skipping")
        conn.close()
        return

    schema_sql = SCHEMA_PATH.read_text()
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()
    logger.info(f"init_db: created tables from {SCHEMA_PATH}")


def run_query(sql: str, params: tuple = ()) -> list[dict]:
    """Execute a read-only SQL query and return results as a list of dicts.

    Uses parameterized queries to prevent SQL injection. Wraps in
    try/except so a bad query doesn't crash the agent.
    """
    conn = get_connection()
    try:
        cursor = conn.execute(sql, params)
        columns = [desc[0] for desc in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        logger.info(f"run_query: returned {len(rows)} rows")
        return rows
    except Exception:
        logger.exception(f"run_query failed: sql={sql!r}")
        return []
    finally:
        conn.close()
