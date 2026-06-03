"""Phase 2 board mechanics tests."""

import sqlite3

import pytest

from server.store import (
    ToolError,
    ack_message,
    init_db,
    read_thread,
    reply_message,
    write_event,
)


def _event(**overrides):
    base = {
        "event_id": "evt-root",
        "thread_id": "phase2-board",
        "agent_id": "claude",
        "kind": "message",
        "timestamp": "2026-06-03T00:00:00+00:00",
        "content_md": "Root message",
        "payload_json": None,
    }
    return {**base, **overrides}


def test_ack_message_is_visible_and_idempotent(tmp_db):
    write_event(tmp_db, _event())

    first = ack_message(tmp_db, "evt-root", "codex")
    second = ack_message(tmp_db, "evt-root", "codex")

    assert first["validation_status"] == "ok"
    assert first["already_acknowledged"] is False
    assert second["ack_id"] == first["ack_id"]
    assert second["already_acknowledged"] is True

    rows = read_thread(tmp_db, "phase2-board")
    assert rows[0]["acks"] == [
        {
            "ack_id": first["ack_id"],
            "agent_id": "codex",
            "delivered_at": first["delivered_at"],
        }
    ]


def test_ack_message_rejects_unknown_message(tmp_db):
    with pytest.raises(ToolError):
        ack_message(tmp_db, "missing", "codex")


def test_reply_message_links_to_parent(tmp_db):
    write_event(tmp_db, _event())

    receipt = reply_message(
        tmp_db,
        thread_id="phase2-board",
        parent_message_id="evt-root",
        agent_id="codex",
        kind="message",
        content_md="Reply from Codex",
    )

    rows = read_thread(tmp_db, "phase2-board")
    assert len(rows) == 2
    assert rows[1]["event_id"] == receipt["event_id"]
    assert rows[1]["parent_event_id"] == "evt-root"
    assert rows[1]["content_md"] == "Reply from Codex"


def test_reply_message_rejects_cross_thread_parent(tmp_db):
    write_event(tmp_db, _event())

    with pytest.raises(ToolError):
        reply_message(
            tmp_db,
            thread_id="other-thread",
            parent_message_id="evt-root",
            agent_id="codex",
            kind="message",
            content_md="Wrong thread",
        )


def test_existing_store_migrates_parent_event_id(tmp_path):
    db_path = str(tmp_path / "legacy.sqlite")
    con = sqlite3.connect(db_path)
    con.executescript(
        """
        CREATE TABLE threads (
            thread_id  TEXT PRIMARY KEY,
            slug       TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            state      TEXT NOT NULL DEFAULT 'open'
        );
        CREATE TABLE events (
            event_id     TEXT PRIMARY KEY,
            thread_id    TEXT NOT NULL REFERENCES threads(thread_id),
            agent_id     TEXT NOT NULL,
            kind         TEXT NOT NULL,
            timestamp    TEXT NOT NULL,
            content_md   TEXT NOT NULL,
            payload_json TEXT
        );
        """
    )
    con.execute(
        "INSERT INTO threads (thread_id, slug, created_at, state) VALUES (?,?,?,?)",
        ("legacy-thread", "legacy-thread", "2026-06-03T00:00:00+00:00", "open"),
    )
    con.execute(
        "INSERT INTO events"
        " (event_id, thread_id, agent_id, kind, timestamp, content_md, payload_json)"
        " VALUES (?,?,?,?,?,?,?)",
        (
            "legacy-event",
            "legacy-thread",
            "claude",
            "message",
            "2026-06-03T00:00:00+00:00",
            "Legacy survives",
            None,
        ),
    )
    con.commit()
    con.close()

    migrated = init_db(db_path)
    rows = read_thread(migrated, "legacy-thread")
    migrated.close()

    assert rows[0]["event_id"] == "legacy-event"
    assert rows[0]["parent_event_id"] is None
    assert rows[0]["acks"] == []
