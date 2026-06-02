"""
SQLite store layer for BMG-Harmony.

Exports:
    init_db(path: str) -> sqlite3.Connection
    write_event(con: sqlite3.Connection, event: dict) -> dict
    read_thread(con: sqlite3.Connection, thread_id: str) -> list[dict]
    list_threads(con: sqlite3.Connection, state: str | None = None) -> list[dict]
"""

import os
import sqlite3
from datetime import datetime, timezone

from jsonschema import ValidationError
from uuid_utils import uuid7

from server.schema import validate_event

# Try to import the real ToolError from mcp; fall back to a local definition
# so this module is usable without the MCP server running (e.g. in tests).
try:
    from mcp.server.fastmcp.exceptions import ToolError
except ImportError:
    class ToolError(Exception):  # type: ignore[no-redef]
        """Fallback ToolError when mcp package is unavailable."""


def init_db(path: str) -> sqlite3.Connection:
    """Open (or create) the SQLite store at *path*.

    Sets WAL mode and synchronous=NORMAL, executes the canonical DDL from
    schema.sql (including append-only triggers), commits, and returns the
    open connection.
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    con = sqlite3.connect(path, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")

    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as fh:
        schema_sql = fh.read()
    con.executescript(schema_sql)
    con.commit()
    return con


def write_event(con: sqlite3.Connection, event: dict) -> dict:
    """Write an event to the store.

    If *event* does not contain 'event_id' or 'timestamp', they are generated
    automatically (callers may supply them for testability).

    Raises ToolError on:
    - jsonschema.ValidationError (missing or invalid required fields)
    - sqlite3.IntegrityError (append-only trigger fired)

    Returns receipt dict: {event_id, thread_id, revision, timestamp, validation_status: "ok"}
    """
    full_event = dict(event)
    if "event_id" not in full_event or not full_event.get("event_id"):
        full_event["event_id"] = str(uuid7())
    if "timestamp" not in full_event or not full_event.get("timestamp"):
        full_event["timestamp"] = datetime.now(timezone.utc).isoformat()

    try:
        validate_event(full_event)
    except ValidationError as exc:
        raise ToolError(f"Event validation failed: {exc.message}") from exc

    try:
        # Auto-create thread; idempotent if slug already exists.
        con.execute(
            "INSERT OR IGNORE INTO threads (thread_id, slug, created_at, state) VALUES (?,?,?,?)",
            (
                full_event["thread_id"],
                full_event["thread_id"],
                datetime.now(timezone.utc).isoformat(),
                "open",
            ),
        )

        con.execute(
            "INSERT INTO events"
            " (event_id, thread_id, agent_id, kind, timestamp, content_md, payload_json)"
            " VALUES (?,?,?,?,?,?,?)",
            (
                full_event["event_id"],
                full_event["thread_id"],
                full_event["agent_id"],
                full_event["kind"],
                full_event["timestamp"],
                full_event["content_md"],
                full_event.get("payload_json"),
            ),
        )

        revision = con.execute("SELECT last_insert_rowid()").fetchone()[0]
        con.commit()

    except sqlite3.IntegrityError as exc:
        raise ToolError("Event store is append-only: mutation refused.") from exc

    return {
        "event_id": full_event["event_id"],
        "thread_id": full_event["thread_id"],
        "revision": int(revision),
        "timestamp": full_event["timestamp"],
        "validation_status": "ok",
    }


def read_thread(con: sqlite3.Connection, thread_id: str) -> list[dict]:
    """Return all events in *thread_id* ordered by insertion (rowid ASC).

    Returns an empty list if the thread does not exist — never raises.
    """
    cur = con.execute(
        "SELECT event_id, thread_id, agent_id, kind, timestamp, content_md, payload_json"
        " FROM events WHERE thread_id=? ORDER BY rowid ASC",
        (thread_id,),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def list_threads(con: sqlite3.Connection, state: str | None = None) -> list[dict]:
    """Return all threads, optionally filtered by *state*.

    Each dict has keys: thread_id, slug, created_at, state.
    """
    if state is not None:
        cur = con.execute(
            "SELECT thread_id, slug, created_at, state FROM threads WHERE state=?",
            (state,),
        )
    else:
        cur = con.execute(
            "SELECT thread_id, slug, created_at, state FROM threads"
        )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
