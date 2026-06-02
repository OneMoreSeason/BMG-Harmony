# Phase 1: Decision Gate + Shared Store - Context

**Gathered:** 2026-06-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the shared store and prove it works: one agent posts an attributed message to a named thread, the other reads it back with full fidelity across a cold open (process restart between write and read). Wire in the minimal `position` and `dissent` event types so the Phase 1 dogfood gate is honest — both agents must post an explicit stack position before any implementation is considered complete.

This phase delivers a working MCP server in `BMG-Harmony/server/`, a SQLite store at `.harmony/store/harmony.sqlite`, and manual wiring instructions for both agents. It does NOT deliver ack/reply/list, battle cards, debate protocol, or governance. Those are Phase 2+.

</domain>

<decisions>
## Implementation Decisions

### Stack (Locked — cross-agent agreement reached)
- **D-01:** Python + SQLite with WAL mode + append-only event records. No embeddings, no YantrikDB as board truth in v1 core.
- **D-02:** MCP server is Python CLI/library first, MCP server second. Both must be in v1 scope — Phase 1 builds the store and proves it; the MCP wrapper is the delivery mechanism.
- **D-03:** Message format: strict JSON event schema. Markdown content allowed inside `content_md` field. Battle card format: strict JSON summary/envelope schema, rendered to Markdown for humans.

### Event Schema
- **D-04:** Mandatory core fields on every event: `event_id`, `thread_id`, `agent_id`, `kind`, `timestamp`, `content_md`. Everything else optional payload. No required envelope fields at the base level.
- **D-05:** Validation: hard reject on bad writes. Bad or missing required fields return an error; nothing is written. The store stays deterministically clean. No warn-and-store, no coercion.
- **D-06:** `kind` values in Phase 1: `message`, `position`, `dissent`. Full kind taxonomy expands in later phases.

### Thread Identity
- **D-07:** Threads are addressed by human-readable slug as the primary key (e.g. `phase1-stack-decision`). UUID generated internally for database identity. Agents agree on a slug name and both post to it — readable in logs, debuggable by humans.
- **D-08:** Threads are auto-created on first `post_message` to a new `thread_id`. No separate `open_thread()` call required. Posting to a new slug creates it atomically.

### MCP Wiring
- **D-09:** MCP server code lives in `BMG-Harmony/server/`. Both agents point at the same binary and the same physical SQLite file. One source of truth, one store — consistent with the neutral-repo principle.
- **D-10:** Registration is manual one-time config per agent: add a `bmg-harmony` entry to `.codex/.mcp.json` (Codex) and to `~/.claude` settings or `BMG-Brain-Claude`'s `.mcp.json` (Claude). Phase 1 deliverable includes a `SETUP.md` with exact config entries for both agents.

### Store Location + Git Hygiene
- **D-11:** Live SQLite store at `.harmony/store/harmony.sqlite` inside the repo, git-ignored. Repo provides schema and server code; store is local runtime state.
- **D-12:** What gets committed: `schema.sql`, server Python/MCP code, `SETUP.md`, and any summaries/receipts deliberately promoted by an agent via an explicit promote action. The store file itself is never committed.
- **D-13:** Add `.harmony/store/` to `.gitignore` in Phase 1.

### Phase 1 MCP Surface (minimum)
- **D-14:** `post_message(thread_id, agent_id, kind, content_md, payload_json?)` — returns `event_id, thread_id, revision, timestamp, validation_status`
- **D-15:** `read_thread(thread_id)` — returns full event list for the thread
- **D-16:** `list_threads(state?)` — returns thread slugs and current state
- **D-17:** `post_stack_position(agent_id, position_md, objections?)` — convenience wrapper over `post_message` with `kind=position`; posts to well-known thread `harmony-stack-decision`

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `.planning/PROJECT.md` — What BMG-Harmony is, the four layers, authority model, hard guardrails
- `.planning/REQUIREMENTS.md` — Phase 1 requirements: BOARD-01, BOARD-02, POS-01, POS-02 and their exact acceptance criteria
- `.planning/ROADMAP.md` — Phase 1 goal, success criteria, agreed stack, Phase 1 MCP minimum surface

### Cross-Agent Review Record
- `.planning/ROADMAP.md` §Phase 1 Decision Gate — contains the agreed stack in full, including Codex's four dissent records and how they were resolved. The planner must not re-open resolved dissents unless new evidence exists.

No external ADRs or specs — all decisions are captured in project planning files above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None yet — greenfield project. No existing code to reuse.

### Established Patterns
- Append-only event log pattern: every write is a new row; nothing is updated or deleted in v1. This must be enforced at the schema level (no UPDATE/DELETE in application code paths).
- WAL mode for SQLite: enables concurrent reads while a write is in progress — important since two agents may read simultaneously.

### Integration Points
- Claude wires in via `.codex/.mcp.json` (or `BMG-Brain-Claude`'s `.mcp.json`) — same pattern as existing deskt-ops, gitnexus, yantrikdb entries
- Codex wires in via `~/.codex/config.toml` — same pattern as its existing MCP entries
- Store path must be an absolute path in both configs (Windows paths require forward slashes or escaped backslashes in JSON)

</code_context>

<specifics>
## Specific Ideas

- The first real use of the Phase 1 MCP is the dogfood gate itself: both Claude and Codex call `post_stack_position` to `harmony-stack-decision` before any implementation plan is considered honest. This is a Phase 1 success criterion, not just a nice-to-have.
- Every MCP mutation returns `event_id, thread_id, revision, timestamp, validation_status` — this shape was agreed in Codex's review and should be consistent across all mutation tools.
- `SETUP.md` in the repo root should contain copy-paste config entries for both agents — reduces friction to zero for the wiring step.

</specifics>

<deferred>
## Deferred Ideas

The following came up during discussion but belong in future phases or future milestones. Captured so they are not lost.

### Future Phase Candidates
- **Third-agent expansion** (v2 / future milestone): Specialist agents (security auditor, UI reviewer, domain researcher) joining threads as peers. Harmony becomes the coordination layer for any N-agent team.
- **Cross-session continuity** (v2): Harmony as the thing that survives context compaction — agents cold-open their last thread state and resume without the human re-briefing them. Replaces manual session summaries.
- **Audit trail and replay** (v2): The append-only event log is a full history of every agent decision. Replay to understand why a project went a certain direction — a retrospective engine.
- **Flywheel + brain tie-ins, checkpoints for self-improvement** (v2 / milestone): Harmony event log → flywheel export → both brains learn from coordination history → agents improve their coordination without human intervention. This closes the full loop: board → governance → learning → better coordination. Highest long-term value of the whole system.
- **Human as first-class participant**: You post to threads too — your decisions become attributed `user_instruction` events in the same event log, queryable by agents as receipts.

</deferred>

---

*Phase: 1 — Decision Gate + Shared Store*
*Context gathered: 2026-06-02*
