"""Phase 2 battle-card and role-surface tests."""

import pytest

from server.store import (
    ToolError,
    append_proving_envelope,
    get_battle_card,
    write_event,
)


def _event(**overrides):
    base = {
        "event_id": "evt-card-root",
        "thread_id": "phase2-card",
        "agent_id": "claude",
        "kind": "position",
        "timestamp": "2026-06-03T00:00:00+00:00",
        "content_md": "Latest decision: proceed with deterministic battle cards.",
        "payload_json": None,
    }
    return {**base, **overrides}


def test_get_battle_card_returns_deterministic_summary(tmp_db):
    write_event(tmp_db, _event())
    write_event(
        tmp_db,
        _event(
            event_id="evt-card-dissent",
            kind="dissent",
            content_md="Open flag proof.",
        ),
    )

    card = get_battle_card(tmp_db, "phase2-card")

    assert card["thread_id"] == "phase2-card"
    assert card["topic"] == "phase2-card"
    assert card["state"] == "open"
    assert card["latest_decision"]["event_id"] == "evt-card-root"
    assert card["latest_event"]["event_id"] == "evt-card-dissent"
    assert card["unacked_count"] == 2
    assert card["dissent_count"] == 1
    assert card["envelope_count"] == 0
    assert "unacked_messages" in card["open_flags"]
    # Phase 3: undelivered dissent now flags as 'undelivered_dissent' (more specific than 'dissent_present')
    assert any(f in card["open_flags"] for f in ("dissent_present", "undelivered_dissent", "dissent_response_pending"))
    assert "missing_proving_envelope" in card["open_flags"]


def test_append_proving_envelope_is_visible_on_card(tmp_db):
    write_event(tmp_db, _event())

    receipt = append_proving_envelope(
        tmp_db,
        thread_id="phase2-card",
        agent_id="codex",
        proved="- Store read path\n- Card assembly",
        not_checked="- MCP transport",
        confidence=0.82,
    )

    card = get_battle_card(tmp_db, "phase2-card")
    envelope = card["latest_envelopes"][0]

    assert receipt["validation_status"] == "ok"
    assert card["envelope_count"] == 1
    assert envelope["envelope_id"] == receipt["envelope_id"]
    assert envelope["proved"] == "- Store read path\n- Card assembly"
    assert envelope["not_checked"] == "- MCP transport"
    assert envelope["confidence"] == 0.82
    assert "missing_proving_envelope" not in card["open_flags"]


def test_append_proving_envelope_rejects_bad_confidence(tmp_db):
    write_event(tmp_db, _event())

    with pytest.raises(ToolError):
        append_proving_envelope(
            tmp_db,
            thread_id="phase2-card",
            agent_id="codex",
            proved="Too confident",
            not_checked="Nothing",
            confidence=1.5,
        )


def test_unknown_battle_card_thread_raises(tmp_db):
    with pytest.raises(ToolError):
        get_battle_card(tmp_db, "missing-thread")


def test_harmony_roles_card_is_board_readable(tmp_db):
    card = get_battle_card(tmp_db, "harmony-roles")
    roles = {role["agent_id"]: role for role in card["roles"]}

    assert set(roles) == {"claude", "codex"}
    assert "supervisor / briefer / reviewer" in roles["claude"]["role_md"]
    assert "executor / builder / Brain 1" in roles["codex"]["role_md"]
    assert "architecture" in roles["claude"]["default_route_for"]
    assert "implementation" in roles["codex"]["default_route_for"]
    assert "domain-partitioned, not hierarchical" in roles["claude"]["role_md"]
