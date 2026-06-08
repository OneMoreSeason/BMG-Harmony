# Phase 3: Structured Dissent + Response Windows - Context

**Gathered:** 2026-06-08
**Status:** Ready for implementation planning handoff

<domain>
## Phase Boundary

Phase 3 turns the Phase 1 minimal `dissent` event into a full structured
dissent workflow. It adds categorized dissent filing, explicit delivery
confirmation, deterministic response-window enforcement, and battle-card
visibility for dissent status.

This phase does not add bounded debate rounds, convergence detection, auto-prod,
human escalation packages, role updates, embeddings, or YantrikDB as board
truth. Those remain Phase 4 and Phase 5 concerns.

</domain>

<requirements>
## Phase 3 Requirement Ledger

- **DISSENT-01:** Any agent can file a typed dissent record on any decision or
  plan. Records are attributed, timestamped, and categorized as `technical`,
  `doctrine`, or `scope`.
- **DISSENT-02:** Silence means agreement only after delivery is confirmed and
  the response window has elapsed. Before that, silence is `no_response`, not
  consent.
- **DISSENT-03:** Dissent records travel with the battle card and are visible
  on cold-open rather than buried in the event history.

</requirements>

<decisions>
## Implementation Decisions

### Dissent Records

- **D-28:** `file_dissent` is the canonical Phase 3 entrypoint for dissent. It
  writes a normal append-only `events` row with `kind='dissent'`, but validates
  a typed payload so dissent records become structured without replacing the
  event log.
- **D-29:** Valid dissent categories are exactly `technical`, `doctrine`, and
  `scope`. Unknown categories fail validation at the store layer and MCP layer.
- **D-30:** Dissent payloads should include at least `category` and may include
  `status`, `response_due_at`, `target_event_id`, and response-window metadata
  as the state machine evolves.

### Delivery Confirmation

- **D-31:** `confirm_delivery(message_id, agent_id)` is a semantic alias over
  the existing append-only ack table. It should return the same durable delivery
  receipt shape as `ack_message` while naming the Phase 3 consent precondition
  explicitly.
- **D-32:** Delivery confirmation remains idempotent per message/agent pair.
  Re-confirming delivery must return the existing receipt, not write duplicate
  rows or mutate event records.

### Response Windows

- **D-33:** Response-window enforcement belongs in deterministic store reads and
  state transitions, not in the FastMCP adapter and not in an LLM summary.
- **D-34:** Before delivery is confirmed, unanswered dissent status is
  `no_response`. After delivery is confirmed but before the window expires,
  status remains pending. After delivery plus expiry, silence becomes recorded
  agreement.
- **D-35:** Agreement-by-silence must be represented as store-derived state or
  an append-only record with evidence fields, not an ambiguous absence of data.

### Battle Cards

- **D-36:** `get_battle_card(thread_id)` must expose recent/open dissent records
  and response-window state on the lean card. It should not force callers to
  read the full thread to discover an active objection.
- **D-37:** Battle-card dissent output should remain compact: counts, latest
  dissent summaries, open dissent flags, and agreement/no_response status are
  enough for cold-open routing.

</decisions>

<canonical_refs>
## Canonical References

Downstream agents must read these before implementation:

- `.planning/PROJECT.md` - core value, role authority, hard guardrails.
- `.planning/REQUIREMENTS.md` - DISSENT-01 through DISSENT-03.
- `.planning/ROADMAP.md` - Phase 3 goal, tools, and success criteria.
- `server/schema.sql` - canonical SQLite DDL source.
- `server/schema.py` - strict JSON schema validation pattern.
- `server/store.py` - store-layer API, append-only writes, battle cards.
- `server/harmony_server.py` - thin FastMCP adapter pattern.
- `tests/test_phase2_board.py` and `tests/test_phase2_battle_card.py` -
  nearest regression style for acks, events, and battle-card visibility.

</canonical_refs>

<code_context>
## Existing Code Insights

### Established Patterns

- `write_event(con, event)` already supports `kind='dissent'`.
- `ack_message(con, message_id, agent_id)` already stores append-only delivery
  proof in `message_acks`.
- `get_battle_card(con, thread_id)` already exposes `dissent_count` and
  `dissent_present`, but does not expose categories, response windows, or
  agreement/no_response state.
- `harmony_server.py` is a thin FastMCP wrapper over store functions; Phase 3
  should keep that adapter non-reasoning.

### Migration Needs

Phase 3 can likely extend the existing event payload model before adding a
dedicated dissent table. If response-window history needs explicit durable
records, prefer an append-only table or append-only event records over updates.
Any live-store migration must be idempotent and preserve Phase 1/2 events.

### Validation Shape

Phase 3 should add focused tests for:

- valid and invalid dissent categories;
- `file_dissent` receipt and readback through `read_thread`;
- `confirm_delivery` idempotence and compatibility with existing acks;
- response-window state before delivery, after delivery before expiry, and after
  delivery plus expiry;
- battle-card cold-open visibility for dissent category and window status;
- MCP tool exposure and simple call smoke for the two new tools.

</code_context>

<deferred>
## Deferred Ideas

- Debate opening, round caps, alternating turns, convergence, and auto-prod are
  Phase 4.
- Impasse routing, human escalation, flywheel export, and role-definition
  updates are Phase 5.
- Semantic dissent clustering and YantrikDB-derived memory are outside v1 core
  board truth.

</deferred>

---

*Phase: 3 - Structured Dissent + Response Windows*
*Context gathered: 2026-06-08*
