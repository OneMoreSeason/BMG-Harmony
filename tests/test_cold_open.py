"""Cold-open proof test for BMG-Harmony.

Verifies that data written in one connection (con1) persists to disk and is
readable by a completely separate connection (con2) opened after con1 is
explicitly closed — simulating a process restart between write and read.
"""

import sqlite3

from server.store import init_db, write_event


def test_cold_open(tmp_path):
    """Write in con1, close it, then read back raw via con2 (no init_db)."""
    db_path = str(tmp_path / "harmony.sqlite")

    # -------------------------------------------------------------------------
    # Write phase — first "process"
    # -------------------------------------------------------------------------
    con1 = init_db(db_path)
    event_id = "evt-cold-open-proof"
    expected_content = "## Cold-open proof — WAL persisted"

    write_event(
        con1,
        {
            "event_id": event_id,
            "thread_id": "cold-open-test",
            "agent_id": "claude",
            "kind": "message",
            "timestamp": "2026-06-02T00:00:00+00:00",
            "content_md": expected_content,
            "payload_json": None,
        },
    )

    # Explicit close — simulates process exit; WAL checkpoint is triggered here.
    con1.close()

    # -------------------------------------------------------------------------
    # Read phase — second "process" (raw sqlite3.connect, NOT init_db)
    # -------------------------------------------------------------------------
    con2 = sqlite3.connect(db_path)
    row = con2.execute(
        "SELECT content_md FROM events WHERE event_id=?",
        (event_id,),
    ).fetchone()
    con2.close()

    assert row is not None, "Event not found after cold open — WAL did not flush to disk"
    assert row[0] == expected_content, f"Content mismatch: got {row[0]!r}"
