"""Unit tests for the BMG-Harmony SQLite store layer."""

import sqlite3

import pytest

from server.store import init_db, list_threads, read_thread, write_event

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE_EVENT = {
    "event_id": "evt-test-001",
    "thread_id": "test-thread",
    "agent_id": "claude",
    "kind": "message",
    "timestamp": "2026-06-02T00:00:00+00:00",
    "content_md": "Hello from test",
    "payload_json": None,
}


def _event(**overrides):
    """Return a copy of _BASE_EVENT with any overrides applied."""
    return {**_BASE_EVENT, **overrides}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_post_message_writes_event(tmp_db):
    """write_event returns a valid receipt; row is readable on the same connection."""
    receipt = write_event(tmp_db, _event())

    # Receipt shape
    assert "event_id" in receipt
    assert "thread_id" in receipt
    assert "revision" in receipt
    assert "timestamp" in receipt
    assert receipt["validation_status"] == "ok"
    assert isinstance(receipt["revision"], int)

    # Row is readable
    rows = read_thread(tmp_db, _BASE_EVENT["thread_id"])
    assert len(rows) == 1
    assert rows[0]["content_md"] == "Hello from test"


def test_post_message_rejects_invalid(tmp_db):
    """write_event raises ToolError for missing required field; no row written."""
    from server.store import ToolError

    bad_event = {
        "event_id": "evt-bad",
        "thread_id": "test-thread",
        # agent_id intentionally missing
        "kind": "message",
        "timestamp": "2026-06-02T00:00:00+00:00",
        "content_md": "This should fail",
    }

    with pytest.raises(ToolError):
        write_event(tmp_db, bad_event)

    # No row should have been written
    rows = read_thread(tmp_db, "test-thread")
    assert rows == []


def test_read_thread(tmp_db):
    """read_thread returns all events in insertion order; empty list for unknown thread."""
    evt1 = _event(event_id="evt-001", content_md="First")
    evt2 = _event(event_id="evt-002", content_md="Second")

    write_event(tmp_db, evt1)
    write_event(tmp_db, evt2)

    rows = read_thread(tmp_db, "test-thread")
    assert len(rows) == 2
    assert rows[0]["content_md"] == "First"
    assert rows[1]["content_md"] == "Second"

    # Each row has all 7 columns
    expected_keys = {"event_id", "thread_id", "agent_id", "kind", "timestamp", "content_md", "payload_json"}
    assert set(rows[0].keys()) == expected_keys

    # Unknown thread returns empty list
    assert read_thread(tmp_db, "no-such-thread") == []


def test_append_only_enforcement(tmp_path):
    """An UPDATE on events raises sqlite3.IntegrityError (not OperationalError)."""
    db_path = str(tmp_path / "harmony.sqlite")
    con = init_db(db_path)
    write_event(con, _event())

    with pytest.raises(sqlite3.IntegrityError):
        con.execute(
            "UPDATE events SET content_md='mutated' WHERE event_id=?",
            (_BASE_EVENT["event_id"],),
        )


def test_post_stack_position(tmp_db):
    """A position event can be written and read back with kind preserved."""
    evt = _event(
        event_id="evt-position-001",
        thread_id="harmony-stack-decision",
        kind="position",
        content_md="Python + SQLite: approved.",
    )
    write_event(tmp_db, evt)

    rows = read_thread(tmp_db, "harmony-stack-decision")
    assert len(rows) == 1
    assert rows[0]["kind"] == "position"


def test_post_dissent(tmp_db):
    """A dissent event can be written and read back with kind preserved."""
    evt = _event(
        event_id="evt-dissent-001",
        thread_id="harmony-stack-decision",
        kind="dissent",
        content_md="I object to the thread state machine being deferred.",
    )
    write_event(tmp_db, evt)

    rows = read_thread(tmp_db, "harmony-stack-decision")
    assert len(rows) == 1
    assert rows[0]["kind"] == "dissent"


def test_list_threads(tmp_db):
    """list_threads returns thread dicts; list_threads(state='open') includes both."""
    # Write two events to different threads so both threads are auto-created.
    write_event(tmp_db, _event(event_id="evt-a1", thread_id="thread-alpha"))
    write_event(tmp_db, _event(event_id="evt-b1", thread_id="thread-beta"))

    all_threads = list_threads(tmp_db)
    assert len(all_threads) >= 2

    # Each dict has the expected keys
    expected_keys = {"thread_id", "slug", "created_at", "state"}
    for t in all_threads:
        assert set(t.keys()) == expected_keys

    # Filter by state='open' includes both (default state is 'open')
    open_threads = list_threads(tmp_db, state="open")
    thread_ids = {t["thread_id"] for t in open_threads}
    assert "thread-alpha" in thread_ids
    assert "thread-beta" in thread_ids
