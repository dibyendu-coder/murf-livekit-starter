"""
database.py — SQLite persistence layer for caller memory.

Provides three public functions used exclusively by the agent's tool methods:
  - init_db()       : create tables on first run
  - lookup_caller() : fetch a caller's record by user_id
  - save_caller()   : upsert (insert or update) a caller's record

The database file is created at caller_memory.db relative to the current
working directory (i.e. backend/ when launched with `uv run python src/agent.py`).
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("database")

# ---------------------------------------------------------------------------
# Database location
# ---------------------------------------------------------------------------

# Place the file in backend/ (one level above src/) so it survives code edits.
_DB_PATH = Path(__file__).parent.parent / "caller_memory.db"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS callers (
    user_id             TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    language_preference TEXT,
    current_level       TEXT,
    topics_covered      TEXT,   -- JSON-encoded list of strings
    mistakes            TEXT,   -- JSON-encoded list of strings
    last_interaction    TEXT    -- ISO-8601 UTC timestamp
);
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def init_db() -> None:
    """Create the database and tables if they do not already exist.

    Safe to call multiple times (idempotent). Called once during agent prewarm.
    """
    logger.info("Initialising caller database at %s", _DB_PATH)
    with _connect() as conn:
        conn.execute(_CREATE_TABLE_SQL)
    logger.info("Database ready.")


def lookup_caller(user_id: str) -> dict[str, Any] | None:
    """Return the stored record for *user_id*, or ``None`` if not found.

    Args:
        user_id: The unique identifier for the caller (LiveKit participant identity).

    Returns:
        A dictionary matching the schema::

            {
                "user_id":             str,
                "name":                str,
                "language_preference": str | None,
                "current_level":       str | None,
                "topics_covered":      list[str],
                "mistakes":            list[str],
                "last_interaction":    str | None,
            }

        or ``None`` if the caller is not in the database.
    """
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM callers WHERE user_id = ?", (user_id,)
        ).fetchone()

    if row is None:
        return None

    return _row_to_dict(row)


def save_caller(record: dict[str, Any]) -> None:
    """Insert or update a caller record (upsert).

    The ``last_interaction`` field is automatically set to the current UTC time.

    Args:
        record: A dictionary with at least ``user_id`` and ``name``. All other
                fields are optional and default to ``None`` / empty list.
    """
    if "user_id" not in record or "name" not in record:
        raise ValueError("record must contain 'user_id' and 'name'")

    now = datetime.now(timezone.utc).isoformat()

    topics = record.get("topics_covered", [])
    mistakes = record.get("mistakes", [])

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO callers
                (user_id, name, language_preference, current_level,
                 topics_covered, mistakes, last_interaction)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name                = excluded.name,
                language_preference = excluded.language_preference,
                current_level       = excluded.current_level,
                topics_covered      = excluded.topics_covered,
                mistakes            = excluded.mistakes,
                last_interaction    = excluded.last_interaction
            """,
            (
                record["user_id"],
                record["name"],
                record.get("language_preference"),
                record.get("current_level"),
                json.dumps(topics if isinstance(topics, list) else [topics]),
                json.dumps(mistakes if isinstance(mistakes, list) else [mistakes]),
                now,
            ),
        )

    logger.info("Saved record for user_id=%s (name=%s)", record["user_id"], record["name"])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _connect() -> sqlite3.Connection:
    """Return an auto-committing connection to the database."""
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a sqlite3.Row to a plain dict, deserialising JSON columns."""
    d = dict(row)
    for key in ("topics_covered", "mistakes"):
        raw = d.get(key)
        try:
            d[key] = json.loads(raw) if raw else []
        except (json.JSONDecodeError, TypeError):
            d[key] = []
    return d
