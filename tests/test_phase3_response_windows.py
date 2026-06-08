"""DISSENT-02: response window state machine — confirm_delivery and window states."""

from datetime import datetime, timedelta, timezone

import pytest

from server.store import (
    confirm_delivery,
    file_dissent,
    init_db,
    response_window_status,
    write_event,
)

try:
    from mcp.server.fastmcp.exceptions import ToolError
except ImportError:
    from server.store import ToolError  # type: ignore[assignment]


@pytest.fixture()
def db(tmp_path):
    return init_db(str(tmp_path / "test.sqlite"))


@pytest.fixture()
def dissent_id(db):
    receipt = file_dissent(db, "t1", "claude", "technical", "I object")
    return receipt["event_id"]


# ── response window states ───────────────────────────────────────────────────

def test_no_response_before_delivery(db, dissent_id):
    state = response_window_status(db, dissent_id)
    assert state["status"] == "no_response"
    assert state["delivery_confirmed"] is False
    assert state["response_deadline"] is None


def test_pending_after_delivery_within_window(db, dissent_id):
    confirm_delivery(db, dissent_id, "codex")
    now = datetime.now(timezone.utc)
    state = response_window_status(db, dissent_id, now=now)
    assert state["status"] == "pending"
    assert state["delivery_confirmed"] is True
    assert state["response_deadline"] is not None


def test_agreement_by_silence_after_window_elapsed(db, dissent_id):
    confirm_delivery(db, dissent_id, "codex")
    # Inject a time well past the default 24h window
    future = datetime.now(timezone.utc) + timedelta(hours=25)
    state = response_window_status(db, dissent_id, now=future)
    assert state["status"] == "agreement_by_silence"
    assert state["delivery_confirmed"] is True


def test_custom_response_window_respected(db):
    receipt = file_dissent(db, "t1", "claude", "scope", "Scoping concern")
    # Manually write a dissent with short window
    from server.store import write_event
    import json
    short_receipt = write_event(db, {
        "thread_id": "t1",
        "agent_id": "claude",
        "kind": "dissent",
        "content_md": "Short window objection",
        "payload_json": json.dumps({"category": "technical", "response_window_hours": 1.0}),
    })
    confirm_delivery(db, short_receipt["event_id"], "codex")
    # 2 hours later = past the 1h window
    future = datetime.now(timezone.utc) + timedelta(hours=2)
    state = response_window_status(db, short_receipt["event_id"], now=future)
    assert state["status"] == "agreement_by_silence"
    assert state["window_hours"] == 1.0


def test_response_window_status_unknown_event_raises(db):
    with pytest.raises(ToolError):
        response_window_status(db, "nonexistent-id")


def test_response_window_status_on_non_dissent_raises(db):
    receipt = write_event(db, {
        "thread_id": "t1", "agent_id": "claude",
        "kind": "message", "content_md": "Not a dissent"
    })
    with pytest.raises(ToolError):
        response_window_status(db, receipt["event_id"])


# ── confirm_delivery ─────────────────────────────────────────────────────────

def test_confirm_delivery_receipt_has_delivery_confirmed(db, dissent_id):
    receipt = confirm_delivery(db, dissent_id, "codex")
    assert receipt["delivery_confirmed"] is True
    assert receipt["message_id"] == dissent_id
    assert receipt["agent_id"] == "codex"


def test_confirm_delivery_idempotent(db, dissent_id):
    r1 = confirm_delivery(db, dissent_id, "codex")
    r2 = confirm_delivery(db, dissent_id, "codex")
    assert r2["already_acknowledged"] is True
    assert r1["ack_id"] == r2["ack_id"]


def test_confirm_delivery_per_agent_independent(db, dissent_id):
    r1 = confirm_delivery(db, dissent_id, "codex")
    r2 = confirm_delivery(db, dissent_id, "claude")
    assert r1["ack_id"] != r2["ack_id"]
    assert r2["already_acknowledged"] is False


def test_confirm_delivery_works_on_any_message_not_just_dissent(db):
    receipt = write_event(db, {
        "thread_id": "t1", "agent_id": "claude",
        "kind": "message", "content_md": "A proposal"
    })
    r = confirm_delivery(db, receipt["event_id"], "codex")
    assert r["delivery_confirmed"] is True
