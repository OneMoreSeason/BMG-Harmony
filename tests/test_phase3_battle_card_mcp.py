"""DISSENT-03: dissent/window visibility on battle cards + MCP exposure."""

from datetime import datetime, timedelta, timezone

import pytest

import server.harmony_server as _hs
from server.store import (
    confirm_delivery,
    file_dissent,
    get_battle_card,
    init_db,
    write_event,
)


@pytest.fixture()
def db(tmp_path):
    return init_db(str(tmp_path / "test.sqlite"))


# ── MCP tool exposure ────────────────────────────────────────────────────────

def test_mcp_tool_list_includes_phase3_tools():
    tools = {t.name for t in _hs.mcp._tool_manager.list_tools()}
    assert "file_dissent" in tools
    assert "confirm_delivery" in tools


def test_mcp_tool_list_still_includes_all_prior_tools():
    tools = {t.name for t in _hs.mcp._tool_manager.list_tools()}
    expected = {
        "post_message", "read_thread", "list_threads", "post_stack_position",
        "ack_message", "reply_message", "get_battle_card", "append_proving_envelope",
        "file_dissent", "confirm_delivery",
    }
    assert expected.issubset(tools)


# ── battle card dissent visibility (DISSENT-03) ──────────────────────────────

def test_battle_card_has_latest_dissents_field(db):
    file_dissent(db, "t1", "claude", "technical", "I object")
    card = get_battle_card(db, "t1")
    assert "latest_dissents" in card


def test_battle_card_dissent_includes_category_and_window_status(db):
    file_dissent(db, "t1", "claude", "doctrine", "Doctrine concern")
    card = get_battle_card(db, "t1")
    assert len(card["latest_dissents"]) == 1
    d = card["latest_dissents"][0]
    assert d["category"] == "doctrine"
    assert d["window_status"] == "no_response"


def test_battle_card_open_flags_undelivered_dissent(db):
    file_dissent(db, "t1", "codex", "scope", "Out of scope")
    card = get_battle_card(db, "t1")
    assert "undelivered_dissent" in card["open_flags"]


def test_battle_card_open_flags_pending_after_delivery(db):
    receipt = file_dissent(db, "t1", "codex", "technical", "Concern")
    confirm_delivery(db, receipt["event_id"], "claude")
    card = get_battle_card(db, "t1")
    assert "dissent_response_pending" in card["open_flags"]


def test_battle_card_dissent_count_matches_latest_dissents(db):
    file_dissent(db, "t1", "claude", "technical", "First")
    file_dissent(db, "t1", "codex", "scope", "Second")
    card = get_battle_card(db, "t1")
    assert card["dissent_count"] == 2
    assert len(card["latest_dissents"]) == 2


def test_battle_card_no_dissents_field_empty(db):
    write_event(db, {"thread_id": "t1", "agent_id": "claude",
                     "kind": "message", "content_md": "Hello"})
    card = get_battle_card(db, "t1")
    assert card["latest_dissents"] == []
    assert card["dissent_count"] == 0


def test_battle_card_backward_compatible_keys(db):
    write_event(db, {"thread_id": "t1", "agent_id": "claude",
                     "kind": "message", "content_md": "Hello"})
    card = get_battle_card(db, "t1")
    # All Phase 2 keys must still be present
    phase2_keys = {
        "thread_id", "topic", "state", "latest_decision", "open_flags",
        "latest_event", "unacked_count", "dissent_count",
        "envelope_count", "latest_envelopes",
    }
    assert phase2_keys.issubset(card.keys())
