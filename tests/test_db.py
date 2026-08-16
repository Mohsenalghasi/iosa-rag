"""Tests for database connection and query helpers."""
import os
import sqlite3
from pathlib import Path

from src.iosa.database.db import init_db, run_query, get_connection


def test_init_creates_tables(tmp_path):
    db_path = str(tmp_path / "test.db")
    os.environ["DB_PATH"] = db_path

    import importlib
    import src.iosa.database.db as db_module
    importlib.reload(db_module)

    db_module.init_db()

    conn = sqlite3.connect(db_path)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    conn.close()

    table_names = [t[0] for t in tables]
    assert "equipment" in table_names
    assert "incidents" in table_names
    assert "maintenance_logs" in table_names


def test_run_query_returns_dicts():
    from src.iosa.database.db import run_query
    result = run_query("SELECT 1 AS value")
    assert len(result) == 1
    assert result[0]["value"] == 1


def test_run_query_bad_sql_returns_empty():
    from src.iosa.database.db import run_query
    result = run_query("SELECT * FROM nonexistent_table_xyz")
    assert result == []
