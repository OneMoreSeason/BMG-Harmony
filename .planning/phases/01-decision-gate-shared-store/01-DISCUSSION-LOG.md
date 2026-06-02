# Phase 1: Decision Gate + Shared Store - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in 01-CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-02
**Phase:** 1 — Decision Gate + Shared Store
**Areas discussed:** Event schema strictness, Thread identity, MCP wiring, Store location + git hygiene, Future scope (deferred)

---

## Event Schema Strictness

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal core | event_id, thread_id, agent_id, kind, timestamp, content_md. Everything else optional. | ✓ |
| Full envelope always | Core + parent_event_id, session_id, confidence, proving_intent on every write. | |
| Kind-specific schemas | Different required fields per event kind. | |

**User's choice:** Minimal core
**Notes:** Simple, easy to extend later. Don't over-engineer the schema before we know what we need.

| Option | Description | Selected |
|--------|-------------|----------|
| Hard reject | Return error, nothing written. Store stays clean. | ✓ |
| Warn and store | Write with validation_warning flag. Permissive. | |
| Coerce and store | Fill missing fields with defaults. Silent data loss risk. | |

**User's choice:** Hard reject
**Notes:** Deterministic store stays clean. Agents must fix writes before retrying.

---

## Thread Identity

| Option | Description | Selected |
|--------|-------------|----------|
| Human-readable slug + auto UUID | Slug is primary address (e.g. phase1-stack-decision). UUID internal. | ✓ |
| Auto UUID only | UUIDs only. Opaque, requires listing to find threads. | |
| UUID with display name | UUID key, display_name metadata. | |

**User's choice:** Human-readable slug + auto UUID
**Notes:** Readable in logs, debuggable by humans. Agents agree on a slug and both post to it.

| Option | Description | Selected |
|--------|-------------|----------|
| Any agent, auto-created on first post | post_message to new thread_id creates it. No setup step. | ✓ |
| Explicit create required | open_thread() must be called first. | |

**User's choice:** Auto-created on first post
**Notes:** Eliminates a failure mode (posting to uncreated thread) and a ceremony step.

---

## MCP Wiring

| Option | Description | Selected |
|--------|-------------|----------|
| In BMG-Harmony repo, both agents point at it | One server, one store. Neutral. | ✓ |
| In BMG-Organelles-Claude, mirrored to Codex | Claude owns server — contradicts neutral-repo principle. | |
| Duplicate servers, one per agent | Two processes, one file. Adds complexity for no benefit. | |

**User's choice:** Server lives in BMG-Harmony repo
**Notes:** Consistent with the neutral-repo principle established in PROJECT.md.

| Option | Description | Selected |
|--------|-------------|----------|
| Manual one-time config update per agent | Add MCP entry to each agent's config once. | ✓ |
| Auto-register via setup script | Script patches both config files. Riskier. | |

**User's choice:** Manual one-time config
**Notes:** Phase 1 includes a SETUP.md with copy-paste config entries for both agents.

---

## Store Location + Git Hygiene

| Option | Description | Selected |
|--------|-------------|----------|
| Inside repo, git-ignored | .harmony/store/harmony.sqlite. Local runtime state. | ✓ |
| Outside repo in shared location | Fully decoupled from git. Path must be configured everywhere. | |
| Configurable via env var | HARMONY_DB_PATH env var. Maximum flexibility. | |

**User's choice:** Inside repo, git-ignored
**Notes:** Repo provides schema and server; store is runtime state.

| Option | Description | Selected |
|--------|-------------|----------|
| Schema + server + promoted Markdown only | Store file never committed. Deliberate promotion only. | ✓ |
| Schema + server + periodic snapshots | Also commit JSON snapshots on a schedule. | |

**User's choice:** Schema + server + promoted Markdown only
**Notes:** Keeps git log clean. Snapshots/summaries only when an agent deliberately promotes them.

---

## Claude's Discretion

None — user made explicit choices on all questions.

---

## Deferred Ideas

- **Third-agent expansion** — specialist agents joining threads as peers in a future milestone
- **Cross-session continuity** — Harmony survives context compaction, agents resume without re-briefing
- **Audit trail and replay** — full history of agent decisions, replayable as a retrospective engine
- **Flywheel + brain tie-ins, checkpoints for self-improvement** — event log → flywheel export → both brains learn from coordination history (user's addition; flagged as highest long-term value)
- **Human as first-class participant** — user posts to threads as attributed `user_instruction` events
