from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "database" / "schema.sql"

DEFAULT_DATABASE_URL = "postgresql://postgres@localhost:5432/testhp_digital_twin"


def database_url() -> str:
    return os.getenv("TESTHP_DATABASE_URL", DEFAULT_DATABASE_URL).strip()


def connect():
    return psycopg.connect(database_url(), row_factory=dict_row)


def ensure_schema() -> None:
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with connect() as conn:
        conn.execute(sql)
        conn.commit()


def status() -> dict[str, Any]:
    try:
        with connect() as conn:
            row = conn.execute("SELECT current_database() AS database, current_user AS user_name, version() AS version").fetchone()
            tables = conn.execute(
                """SELECT count(*) AS count FROM information_schema.tables
                   WHERE table_schema = 'public' AND table_name IN
                   ('subjects','hands','timepoints','datasets','observations','stage_records')"""
            ).fetchone()
        return {
            "configured": True,
            "connected": True,
            "database": row["database"],
            "user": row["user_name"],
            "schema_tables": tables["count"],
        }
    except Exception as exc:
        return {
            "configured": bool(database_url()),
            "connected": False,
            "database": None,
            "user": None,
            "schema_tables": 0,
            "error": f"{type(exc).__name__}: {exc}",
        }
