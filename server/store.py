"""SQLite store layer for BMG-Harmony."""

import json
import os
import sqlite3
from datetime import datetime, timezone

from jsonschema import ValidationError
from uuid_utils import uuid7

from server.schema import validate_ack, validate_event, validate_proving_envelope

# Try to import the real ToolError from mcp; fall back to a local definition
# so this module is usable without the MCP server running (e.g. in tests).
try:
    from mcp.server.fastmcp.exceptions import ToolError
except ImportError:
    class ToolError(Exception):  # type: ignore[no-redef]
        """Fallback ToolError when mcp package is unavailable."""


ROLE_DEFINITIONS = {
    "claude": {
        "role_md": (
            "Claude is the supervisor / briefer / reviewer. "
            "Claude is the default recommendation route for doctrine, "
            "architecture, coordination law, and review framing."
        ),
        "authority_domains": ["doctrine", "architecture", "coordination_law", "review"],
        "default_route_for": ["doctrine", "architecture"],
    },
    "codex": {
        "role_md": (
            "Codex is the executor / builder / Brain 1. "
            "Codex is the default recommendation route for implementation, "
            "runtime, build decisions, and code/test execution."
        ),
        "authority_domains": ["implementation", "runtime", "build", "tests"],
        "default_route_for": ["implementation", "runtime"],
    },
}

ROLE_AUTHORITY_NOTE = (
    "Role authority is domain-partitioned, not hierarchical. User instruction, "
    "project law, safety gates, and evidence can override either default route. "
    "Either agent may dissent when the domain route is technically wrong or "
    "under-evidenced."
)


def init_db(path: str) -> sqlite3.Connection:
    """Open or create the SQLite store at *path*.

    The schema is idempotent and includes Phase 2 migrations for stores created
    during Phase 1.
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    con = sqlite3.connect(path, check_same_thread=False)
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")

    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as fh:
        schema_sql = fh.read()
    con.executescript(schema_sql)
    _migrate_existing_schema(con)
    _seed_role_definitions(con)
    con.commit()
    return con


def write_event(con: sqlite3.Connection, event: dict) -> dict:
    """Write an event to the append-only store."""
    full_event = dict(event)
    if "event_id" not in full_event or not full_event.get("event_id"):
        full_event["event_id"] = str(uuid7())
    if "timestamp" not in full_event or not full_event.get("timestamp"):
        full_event["timestamp"] = _utc_now()

    try:
        validate_event(full_event)
    except ValidationError as exc:
        raise ToolError(f"Event validation failed: {exc.message}") from exc

    parent_event_id = full_event.get("parent_event_id")
    if parent_event_id:
        _validate_parent_event(con, full_event["thread_id"], parent_event_id)

    try:
        con.execute(
            "INSERT OR IGNORE INTO threads (thread_id, slug, created_at, state)"
            " VALUES (?,?,?,?)",
            (
                full_event["thread_id"],
                full_event["thread_id"],
                _utc_now(),
                "open",
            ),
        )

        con.execute(
            "INSERT INTO events"
            " (event_id, thread_id, agent_id, kind, timestamp, content_md, payload_json, parent_event_id)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (
                full_event["event_id"],
                full_event["thread_id"],
                full_event["agent_id"],
                full_event["kind"],
                full_event["timestamp"],
                full_event["content_md"],
                full_event.get("payload_json"),
                full_event.get("parent_event_id"),
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


def ack_message(con: sqlite3.Connection, message_id: str, agent_id: str) -> dict:
    """Acknowledge delivery of an event for an agent.

    The operation is append-only and idempotent per message/agent pair.
    """
    target = con.execute(
        "SELECT event_id FROM events WHERE event_id=?",
        (message_id,),
    ).fetchone()
    if target is None:
        raise ToolError(f"Message not found: {message_id}")

    existing = con.execute(
        "SELECT ack_id, message_id, agent_id, delivered_at"
        " FROM message_acks WHERE message_id=? AND agent_id=?",
        (message_id, agent_id),
    ).fetchone()
    if existing is not None:
        return {
            "ack_id": existing[0],
            "message_id": existing[1],
            "agent_id": existing[2],
            "delivered_at": existing[3],
            "validation_status": "ok",
            "already_acknowledged": True,
        }

    ack = {
        "ack_id": str(uuid7()),
        "message_id": message_id,
        "agent_id": agent_id,
        "delivered_at": _utc_now(),
    }

    try:
        validate_ack(ack)
    except ValidationError as exc:
        raise ToolError(f"Ack validation failed: {exc.message}") from exc

    try:
        con.execute(
            "INSERT INTO message_acks (ack_id, message_id, agent_id, delivered_at)"
            " VALUES (?,?,?,?)",
            (
                ack["ack_id"],
                ack["message_id"],
                ack["agent_id"],
                ack["delivered_at"],
            ),
        )
        con.commit()
    except sqlite3.IntegrityError as exc:
        raise ToolError("Message acknowledgement could not be written.") from exc

    return {
        **ack,
        "validation_status": "ok",
        "already_acknowledged": False,
    }


def reply_message(
    con: sqlite3.Connection,
    thread_id: str,
    parent_message_id: str,
    agent_id: str,
    kind: str,
    content_md: str,
) -> dict:
    """Post a structurally linked reply in the same thread as its parent."""
    _validate_parent_event(con, thread_id, parent_message_id)
    return write_event(
        con,
        {
            "thread_id": thread_id,
            "agent_id": agent_id,
            "kind": kind,
            "content_md": content_md,
            "payload_json": None,
            "parent_event_id": parent_message_id,
        },
    )


def read_thread(con: sqlite3.Connection, thread_id: str) -> list[dict]:
    """Return all events in *thread_id* ordered by insertion."""
    cur = con.execute(
        "SELECT event_id, thread_id, agent_id, kind, timestamp, content_md, payload_json, parent_event_id"
        " FROM events WHERE thread_id=? ORDER BY rowid ASC",
        (thread_id,),
    )
    cols = [d[0] for d in cur.description]
    events = [dict(zip(cols, row)) for row in cur.fetchall()]
    if not events:
        return []

    event_ids = [event["event_id"] for event in events]
    placeholders = ",".join("?" for _ in event_ids)
    ack_cur = con.execute(
        "SELECT ack_id, message_id, agent_id, delivered_at"
        f" FROM message_acks WHERE message_id IN ({placeholders})"
        " ORDER BY rowid ASC",
        event_ids,
    )
    acks_by_message = {event_id: [] for event_id in event_ids}
    for ack_id, message_id, agent_id, delivered_at in ack_cur.fetchall():
        acks_by_message[message_id].append(
            {
                "ack_id": ack_id,
                "agent_id": agent_id,
                "delivered_at": delivered_at,
            }
        )

    for event in events:
        event["acks"] = acks_by_message[event["event_id"]]

    return events


def list_threads(con: sqlite3.Connection, state: str | None = None) -> list[dict]:
    """Return all threads, optionally filtered by *state*."""
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


def append_proving_envelope(
    con: sqlite3.Connection,
    thread_id: str,
    agent_id: str,
    proved: str,
    not_checked: str,
    confidence: float,
) -> dict:
    """Append a proving-intent envelope to a thread."""
    if not _thread_exists(con, thread_id):
        raise ToolError(f"Thread not found: {thread_id}")

    envelope = {
        "envelope_id": str(uuid7()),
        "thread_id": thread_id,
        "agent_id": agent_id,
        "timestamp": _utc_now(),
        "proved": proved,
        "not_checked": not_checked,
        "confidence": float(confidence),
    }

    try:
        validate_proving_envelope(envelope)
    except ValidationError as exc:
        raise ToolError(f"Proving envelope validation failed: {exc.message}") from exc

    try:
        con.execute(
            "INSERT INTO proving_envelopes"
            " (envelope_id, thread_id, agent_id, timestamp, proved, not_checked, confidence)"
            " VALUES (?,?,?,?,?,?,?)",
            (
                envelope["envelope_id"],
                envelope["thread_id"],
                envelope["agent_id"],
                envelope["timestamp"],
                envelope["proved"],
                envelope["not_checked"],
                envelope["confidence"],
            ),
        )
        con.commit()
    except sqlite3.IntegrityError as exc:
        raise ToolError("Proving envelope could not be written.") from exc

    return {
        "envelope_id": envelope["envelope_id"],
        "thread_id": envelope["thread_id"],
        "agent_id": envelope["agent_id"],
        "timestamp": envelope["timestamp"],
        "validation_status": "ok",
    }


def get_battle_card(con: sqlite3.Connection, thread_id: str) -> dict:
    """Return a deterministic lean battle card for a thread."""
    thread = con.execute(
        "SELECT thread_id, slug, created_at, state FROM threads WHERE thread_id=?",
        (thread_id,),
    ).fetchone()
    if thread is None:
        raise ToolError(f"Thread not found: {thread_id}")

    latest_event = _latest_event(con, thread_id)
    latest_position = _latest_position(con, thread_id)
    unacked_count = _unacked_count(con, thread_id)
    dissent_count = _dissent_count(con, thread_id)
    envelope_count = _envelope_count(con, thread_id)
    latest_envelopes = _latest_envelopes(con, thread_id)

    open_flags = []
    if unacked_count:
        open_flags.append("unacked_messages")
    if dissent_count:
        open_flags.append("dissent_present")
    if latest_event is not None and envelope_count == 0:
        open_flags.append("missing_proving_envelope")

    card = {
        "thread_id": thread[0],
        "topic": thread[1],
        "state": thread[3],
        "latest_decision": latest_position or latest_event,
        "open_flags": open_flags,
        "latest_event": latest_event,
        "unacked_count": int(unacked_count),
        "dissent_count": int(dissent_count),
        "envelope_count": int(envelope_count),
        "latest_envelopes": latest_envelopes,
    }

    if thread_id == "harmony-roles":
        card["roles"] = _read_roles(con)

    return card


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _migrate_existing_schema(con: sqlite3.Connection) -> None:
    event_columns = {
        row[1]
        for row in con.execute("PRAGMA table_info(events)").fetchall()
    }
    if "parent_event_id" not in event_columns:
        con.execute(
            "ALTER TABLE events ADD COLUMN parent_event_id TEXT REFERENCES events(event_id)"
        )


def _seed_role_definitions(con: sqlite3.Connection) -> None:
    created_at = _utc_now()
    con.execute(
        "INSERT OR IGNORE INTO threads (thread_id, slug, created_at, state)"
        " VALUES (?,?,?,?)",
        ("harmony-roles", "harmony-roles", created_at, "open"),
    )

    for agent_id, role in ROLE_DEFINITIONS.items():
        con.execute(
            "INSERT OR IGNORE INTO role_definitions"
            " (agent_id, role_md, authority_domains_json, default_route_for_json, created_at)"
            " VALUES (?,?,?,?,?)",
            (
                agent_id,
                f"{role['role_md']}\n\n{ROLE_AUTHORITY_NOTE}",
                json.dumps(role["authority_domains"]),
                json.dumps(role["default_route_for"]),
                created_at,
            ),
        )


def _validate_parent_event(
    con: sqlite3.Connection,
    thread_id: str,
    parent_event_id: str,
) -> None:
    parent_row = con.execute(
        "SELECT thread_id FROM events WHERE event_id=?",
        (parent_event_id,),
    ).fetchone()
    if parent_row is None:
        raise ToolError(f"Parent event not found: {parent_event_id}")
    if parent_row[0] != thread_id:
        raise ToolError("Parent event belongs to a different thread.")


def _thread_exists(con: sqlite3.Connection, thread_id: str) -> bool:
    return con.execute(
        "SELECT 1 FROM threads WHERE thread_id=?",
        (thread_id,),
    ).fetchone() is not None


def _latest_event(con: sqlite3.Connection, thread_id: str) -> dict | None:
    row = con.execute(
        "SELECT event_id, thread_id, agent_id, kind, timestamp, content_md, payload_json, parent_event_id"
        " FROM events WHERE thread_id=? ORDER BY rowid DESC LIMIT 1",
        (thread_id,),
    ).fetchone()
    if row is None:
        return None
    keys = [
        "event_id",
        "thread_id",
        "agent_id",
        "kind",
        "timestamp",
        "content_md",
        "payload_json",
        "parent_event_id",
    ]
    return dict(zip(keys, row))


def _latest_position(con: sqlite3.Connection, thread_id: str) -> dict | None:
    row = con.execute(
        "SELECT event_id, thread_id, agent_id, kind, timestamp, content_md, payload_json, parent_event_id"
        " FROM events WHERE thread_id=? AND kind='position' ORDER BY rowid DESC LIMIT 1",
        (thread_id,),
    ).fetchone()
    if row is None:
        return None
    keys = [
        "event_id",
        "thread_id",
        "agent_id",
        "kind",
        "timestamp",
        "content_md",
        "payload_json",
        "parent_event_id",
    ]
    return dict(zip(keys, row))


def _unacked_count(con: sqlite3.Connection, thread_id: str) -> int:
    return con.execute(
        "SELECT COUNT(*)"
        " FROM events e"
        " WHERE e.thread_id=?"
        " AND NOT EXISTS (SELECT 1 FROM message_acks a WHERE a.message_id=e.event_id)",
        (thread_id,),
    ).fetchone()[0]


def _dissent_count(con: sqlite3.Connection, thread_id: str) -> int:
    return con.execute(
        "SELECT COUNT(*) FROM events WHERE thread_id=? AND kind='dissent'",
        (thread_id,),
    ).fetchone()[0]


def _envelope_count(con: sqlite3.Connection, thread_id: str) -> int:
    return con.execute(
        "SELECT COUNT(*) FROM proving_envelopes WHERE thread_id=?",
        (thread_id,),
    ).fetchone()[0]


def _latest_envelopes(con: sqlite3.Connection, thread_id: str) -> list[dict]:
    cur = con.execute(
        "SELECT envelope_id, thread_id, agent_id, timestamp, proved, not_checked, confidence"
        " FROM proving_envelopes WHERE thread_id=? ORDER BY rowid DESC LIMIT 3",
        (thread_id,),
    )
    keys = [
        "envelope_id",
        "thread_id",
        "agent_id",
        "timestamp",
        "proved",
        "not_checked",
        "confidence",
    ]
    return [dict(zip(keys, row)) for row in cur.fetchall()]


def _read_roles(con: sqlite3.Connection) -> list[dict]:
    cur = con.execute(
        "SELECT agent_id, role_md, authority_domains_json, default_route_for_json, created_at"
        " FROM role_definitions ORDER BY agent_id ASC"
    )
    roles = []
    for agent_id, role_md, domains, default_routes, created_at in cur.fetchall():
        roles.append(
            {
                "agent_id": agent_id,
                "role_md": role_md,
                "authority_domains": json.loads(domains),
                "default_route_for": json.loads(default_routes),
                "created_at": created_at,
            }
        )
    return roles
