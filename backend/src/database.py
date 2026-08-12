"""
database.py — SQLite persistence layer for caller memory and escalations.

Public functions for caller memory (used by agent tool methods):
  - init_db()                   : create all tables on first run (idempotent)
  - lookup_caller()             : fetch a caller's record by user_id
  - save_caller()               : upsert (insert or update) a caller's record

Public functions for human-help escalations (Day 7):
  - create_escalation()         : insert a new escalation, return HELP-XXXX id
  - list_escalations()          : return all escalations, newest first
  - update_escalation_status()  : change status to OPEN / IN_PROGRESS / RESOLVED

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

_CREATE_CALLERS_SQL = """
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
# Escalations schema (Day 7 — Human Help)
# ---------------------------------------------------------------------------

_CREATE_ESCALATIONS_SQL = """
CREATE TABLE IF NOT EXISTS escalations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    reference_id        TEXT UNIQUE NOT NULL,
    learner_id          TEXT NOT NULL,
    learner_name        TEXT,
    reason              TEXT NOT NULL,
    topic               TEXT,
    summary             TEXT NOT NULL,
    agent_actions       TEXT,           -- JSON-encoded list of strings
    urgency             TEXT DEFAULT 'normal',
    language            TEXT,
    preferred_follow_up TEXT,
    status              TEXT DEFAULT 'OPEN',
    created_at          TEXT NOT NULL   -- ISO-8601 UTC timestamp
);
"""

_VALID_STATUSES = {"OPEN", "IN_PROGRESS", "RESOLVED"}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def init_db() -> None:
    """Create the database and all tables if they do not already exist.

    Safe to call multiple times (idempotent). Called once during agent prewarm.
    Creates both the `callers` table and the `escalations` table (Day 7).
    """
    logger.info("Initialising caller database at %s", _DB_PATH)
    with _connect() as conn:
        conn.execute(_CREATE_CALLERS_SQL)
        conn.execute(_CREATE_ESCALATIONS_SQL)
    logger.info("Database ready (callers + escalations tables).")


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
# Escalation functions (Day 7 — Human Help)
# ---------------------------------------------------------------------------

import random


def _generate_reference_id() -> str:
    """Generate a unique human-readable reference ID like HELP-1042."""
    number = random.randint(1000, 9999)
    return f"HELP-{number}"


def create_escalation(
    learner_id: str,
    reason: str,
    summary: str,
    learner_name: str | None = None,
    topic: str | None = None,
    agent_actions: list[str] | None = None,
    urgency: str = "normal",
    language: str | None = None,
    preferred_follow_up: str | None = None,
) -> dict[str, Any]:
    """Insert a new human-help escalation record into the database.

    Generates a unique HELP-XXXX reference ID.  Retries up to 10 times if
    the generated ID happens to collide with an existing record (extremely rare
    in practice but handled safely).

    Security: stores only the minimum information a teacher needs.
    Never stores passwords, OTPs, PINs, API keys, or full transcripts.

    Args:
        learner_id:           Safe learner identifier (e.g. LiveKit participant id).
        reason:               Short reason for escalation (e.g. "Learner frustrated").
        summary:              Human-readable summary for the teacher.
        learner_name:         Learner's first name or display name (optional).
        topic:                Relevant learning topic, if known (optional).
        agent_actions:        List of things the agent already tried (optional).
        urgency:              "normal" or "high" (defaults to "normal").
        language:             Learner's language / preferred language (optional).
        preferred_follow_up:  How the teacher should follow up, e.g. "voice call" (optional).

    Returns:
        {"success": True,  "reference_id": "HELP-XXXX"}  on success.
        {"success": False, "error": "<reason>"}           on failure.
    """
    now = datetime.now(timezone.utc).isoformat()
    actions_json = json.dumps(agent_actions or [])

    # Retry up to 10 times to avoid the (extremely unlikely) reference_id collision.
    for attempt in range(10):
        ref_id = _generate_reference_id()
        try:
            with _connect() as conn:
                conn.execute(
                    """
                    INSERT INTO escalations
                        (reference_id, learner_id, learner_name, reason, topic,
                         summary, agent_actions, urgency, language,
                         preferred_follow_up, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
                    """,
                    (
                        ref_id,
                        learner_id,
                        learner_name,
                        reason,
                        topic,
                        summary,
                        actions_json,
                        urgency or "normal",
                        language,
                        preferred_follow_up,
                        now,
                    ),
                )
            logger.info(
                "Escalation created: reference_id=%s learner_id=%s",
                ref_id,
                learner_id,
            )
            return {"success": True, "reference_id": ref_id}
        except sqlite3.IntegrityError:
            # reference_id collision — regenerate and retry
            logger.warning(
                "reference_id collision on %s (attempt %d), retrying", ref_id, attempt + 1
            )
            continue
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to create escalation: %s", exc, exc_info=True)
            return {"success": False, "error": "Database error while creating escalation."}

    logger.error("Could not generate a unique reference_id after 10 attempts.")
    return {"success": False, "error": "Could not generate a unique reference ID."}


def list_escalations() -> list[dict[str, Any]]:
    """Return all escalation records ordered newest-first.

    Returns:
        A list of dicts, each matching the escalations table schema.
        Returns an empty list if there are no records or on error.
    """
    try:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT * FROM escalations ORDER BY created_at DESC"
            ).fetchall()
        return [_escalation_row_to_dict(row) for row in rows]
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to list escalations: %s", exc, exc_info=True)
        return []


def update_escalation_status(reference_id: str, new_status: str) -> dict[str, Any]:
    """Update the status of an escalation record.

    Args:
        reference_id: The HELP-XXXX reference ID.
        new_status:   One of "OPEN", "IN_PROGRESS", or "RESOLVED".

    Returns:
        {"success": True}  on success.
        {"success": False, "error": "<reason>"}  on failure.
    """
    if new_status not in _VALID_STATUSES:
        return {
            "success": False,
            "error": f"Invalid status '{new_status}'. Must be one of: {sorted(_VALID_STATUSES)}",
        }
    try:
        with _connect() as conn:
            result = conn.execute(
                "UPDATE escalations SET status = ? WHERE reference_id = ?",
                (new_status, reference_id),
            )
        if result.rowcount == 0:
            return {"success": False, "error": f"Escalation {reference_id} not found."}
        logger.info("Escalation %s status updated to %s", reference_id, new_status)
        return {"success": True}
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Failed to update escalation %s: %s", reference_id, exc, exc_info=True
        )
        return {"success": False, "error": "Database error while updating status."}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _connect() -> sqlite3.Connection:
    """Return an auto-committing connection to the database."""
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a callers sqlite3.Row to a plain dict, deserialising JSON columns."""
    d = dict(row)
    for key in ("topics_covered", "mistakes"):
        raw = d.get(key)
        try:
            d[key] = json.loads(raw) if raw else []
        except (json.JSONDecodeError, TypeError):
            d[key] = []
    return d


def _escalation_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Convert an escalations sqlite3.Row to a plain dict, deserialising JSON columns."""
    d = dict(row)
    raw = d.get("agent_actions")
    try:
        d["agent_actions"] = json.loads(raw) if raw else []
    except (json.JSONDecodeError, TypeError):
        d["agent_actions"] = []
    return d
