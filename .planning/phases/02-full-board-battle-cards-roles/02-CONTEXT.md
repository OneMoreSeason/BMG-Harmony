# Phase 2: Full Board + Battle Cards + Roles - Context

**Gathered:** 2026-06-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 completes the async board layer enough that either agent can cold-open
a thread and know what happened without reading the full transcript first.

This phase adds ack, reply, open-thread visibility, lean battle cards,
append-only proving envelopes, and readable role definitions for Claude and
Codex. It does not add full dissent response windows, debate round caps,
auto-prod, impasse governance, human escalation packages, embeddings, or
YantrikDB-as-board-truth. Those stay in later phases.

</domain>

<requirements>
## Phase 2 Requirement Ledger

- **BOARD-03:** Any agent can acknowledge a message; delivery is visible in
  thread history.
- **BOARD-04:** Any agent can reply to a specific message; the reply is linked
  structurally to its parent.
- **BOARD-05:** Any agent can list open threads and their current state.
- **CARD-01:** Every thread has a lean summary battle card: topic, state,
  latest decision, and open flags.
- **CARD-02:** Every thread has a proving-intent envelope layer.
- **CARD-03:** Lean summary is current on every exchange; envelopes append and
  are never overwritten.
- **ROLES-01:** Claude and Codex role definitions are readable from the board.
- **ROLES-02:** Authority domains are explicit and readable: doctrine and
  architecture route to supervisor by default; implementation and runtime route
  to executor by default.

</requirements>

<decisions>
## Implementation Decisions

### Board Mechanics

- **D-18:** Phase 2 extends the existing store and MCP adapter. It must not
  replace the Phase 1 event log or introduce a second storage engine.
- **D-19:** Acknowledgements are append-only records in a dedicated table, not
  mutations of `events`. The user-facing `delivered_at` value is visible through
  `read_thread` by joining ack records back onto each event.
- **D-20:** Replies use a structural `parent_event_id` link on event rows.
  Existing Phase 1 events have `NULL` parent links. `reply_message` validates
  that the parent exists in the same thread before writing.
- **D-21:** `list_threads(state?)` remains the board listing tool. It may add
  useful thread-state metadata, but Phase 2 does not add a separate
  `list_open_threads` MCP tool.

### Battle Cards

- **D-22:** `get_battle_card(thread_id)` returns a deterministic lean summary
  assembled from current store state. It is not an LLM-generated summary and it
  does not own reasoning authority.
- **D-23:** Topic defaults to thread slug/thread_id. Current state comes from
  `threads.state`. Latest decision is derived from the latest `position` event
  when present, else the latest event. Open flags are deterministic signals such
  as unacked messages, dissent events, missing proving envelopes, and unknown
  thread state.
- **D-24:** Proving envelopes are append-only records. They name what an agent
  claims to have proved, what was not checked, and a handoff confidence value.
  Envelopes are not overwritten by later messages.

### Roles

- **D-25:** Role definitions are board-readable seed data, not hardcoded prose
  hidden only in docs. Phase 2 can seed a small roles surface from `init_db`
  using idempotent inserts.
- **D-26:** Roles are domain-partitioned, not hierarchical. Claude is the
  default route for doctrine/architecture review. Codex is the default route
  for implementation/runtime/build decisions. User instruction, project law,
  safety, and evidence override either route.
- **D-27:** Phase 2 can make role definitions readable but not updatable. Role
  update mechanics are explicitly Phase 5 (`ROLES-03`).

</decisions>

<canonical_refs>
## Canonical References

Downstream agents must read these before implementation:

- `.planning/PROJECT.md` - core value, role authority, hard guardrails.
- `.planning/REQUIREMENTS.md` - BOARD-03 through ROLES-02.
- `.planning/ROADMAP.md` - Phase 2 goal, tools, success criteria.
- `server/schema.sql` - canonical SQLite DDL source.
- `server/schema.py` - strict JSON schema validation pattern.
- `server/store.py` - store-layer API and append-only write pattern.
- `server/harmony_server.py` - thin FastMCP adapter pattern.
- `tests/test_store.py` and `tests/test_cold_open.py` - local test style.

</canonical_refs>

<code_context>
## Existing Code Insights

### Established Patterns

- `init_db(path)` opens SQLite, sets WAL and synchronous NORMAL, runs
  `schema.sql`, commits, and returns a connection.
- `write_event(con, event)` is the central append-only event writer. It
  generates UUID7 event IDs and ISO timestamps when omitted, validates through
  `server/schema.py`, auto-creates threads, inserts the event, commits, and
  returns a small receipt.
- `read_thread(con, thread_id)` currently returns flat event dicts in row order.
- `list_threads(con, state)` currently returns thread rows with
  `thread_id`, `slug`, `created_at`, and `state`.
- `harmony_server.py` imports store functions and exposes one FastMCP tool per
  store operation. Logging stays on stderr; stdout belongs to MCP stdio.

### Migration Needs

The live SQLite store already exists. Fresh DB DDL in `schema.sql` is not
enough for Phase 2. `init_db` needs idempotent migration helpers for existing
stores, including at minimum:

- adding `events.parent_event_id` if missing;
- creating append-only ack/proving-envelope/role tables if missing;
- preserving existing Phase 1 events and dogfood posts.

### Validation Shape

Phase 2 should add focused store tests before or alongside implementation:

- ack receipt and visibility through `read_thread`;
- reply parent validation and `parent_event_id` readback;
- `list_threads(state="open")` still works and includes current metadata;
- battle card cold-open is sufficient without reading every event;
- proving envelopes append and survive cold open;
- role definitions are readable from the board;
- schema validation rejects malformed new records.

</code_context>

<deferred>
## Deferred Ideas

- Full dissent categories and response-window enforcement remain Phase 3.
- Debate state machine, round cap, convergence, and auto-prod remain Phase 4.
- Role updates, impasse routing, human escalation summaries, and flywheel
  export remain Phase 5.
- Embeddings, semantic search, and YantrikDB as board truth remain out of scope
  for v1 core.

</deferred>

---

*Phase: 2 - Full Board + Battle Cards + Roles*
*Context gathered: 2026-06-03*
