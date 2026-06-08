"""DISSENT-01: structured dissent records — file_dissent store operation."""

import json
import pytest

from server.store import file_dissent, init_db, read_thread, write_event

try:
    from mcp.server.fastmcp.exceptions import ToolError
except ImportError:
    from server.store import ToolError  # type: ignore[assignment]


@pytest.fixture()
def db(tmp_path):
    return init_db(str(tmp_path / "test.sqlite"))


@pytest.mark.parametrize("category", ["technical", "doctrine", "scope"])
def test_valid_categories(db, category):
    receipt = file_dissent(db, "t1", "claude", category, f"Objection: {category}")
    assert receipt["validation_status"] == "ok"
    assert receipt["thread_id"] == "t1"
    assert "event_id" in receipt
    assert "timestamp" in receipt


def test_invalid_category_raises_before_store_mutation(db):
    with pytest.raises(ToolError, match="[Dd]issent"):
        file_dissent(db, "t1", "claude", "strategy", "bad category")
    # Thread should not have been created or written
    events = read_thread(db, "t1")
    assert events == []


def test_receipt_shape(db):
    receipt = file_dissent(db, "t1", "codex", "technical", "My concern")
    assert set(receipt.keys()) == {"event_id", "thread_id", "revision", "timestamp", "validation_status"}


def test_dissent_readable_via_read_thread(db):
    receipt = file_dissent(db, "t1", "claude", "doctrine", "I disagree with this approach")
    events = read_thread(db, "t1")
    assert len(events) == 1
    ev = events[0]
    assert ev["kind"] == "dissent"
    assert ev["agent_id"] == "claude"
    payload = json.loads(ev["payload_json"])
    assert payload["category"] == "doctrine"


def test_multiple_dissents_are_append_only(db):
    file_dissent(db, "t1", "claude", "technical", "First objection")
    file_dissent(db, "t1", "codex", "scope", "Second objection")
    events = read_thread(db, "t1")
    assert len(events) == 2
    kinds = [e["kind"] for e in events]
    assert all(k == "dissent" for k in kinds)


def test_dissent_coexists_with_regular_messages(db):
    write_event(db, {"thread_id": "t1", "agent_id": "claude", "kind": "message", "content_md": "Proposal"})
    file_dissent(db, "t1", "codex", "scope", "Out of scope")
    events = read_thread(db, "t1")
    assert len(events) == 2
    assert events[0]["kind"] == "message"
    assert events[1]["kind"] == "dissent"
