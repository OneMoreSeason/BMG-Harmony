# Roadmap — BMG-Harmony v1

*Restructured after cross-agent review (Claude + Codex). Codex dissents incorporated: dissent primitives moved to Phase 1; roles surface moved to Phase 2; structured dissent pulled before debate; DEBATE-05 summary split from governance summary.*

## Phases

- [ ] **Phase 1: Decision Gate + Shared Store** — Tech stack agreed; post/read proven; minimal position + dissent event types exist. First dogfood of the protocol.
- [ ] **Phase 2: Full Board + Battle Cards + Roles** — Complete async board (ack, reply, list) with tiered battle cards and readable role definitions.
- [ ] **Phase 3: Structured Dissent + Response Windows** — Full dissent UX with delivery proof; silence = agreement only after confirmed delivery + elapsed window.
- [ ] **Phase 4: Debate Protocol + Token Discipline + Auto-prod** — Bounded debate with scope gate, round cap, convergence detection, request-only auto-prod, and debate-close summary.
- [ ] **Phase 5: Governance Layer** — Impasse classification, domain routing, human escalation, flywheel encoding, governance summaries, updatable role boundaries.

---

## Phase Details

### Phase 1: Decision Gate + Shared Store

**Goal**: Both agents have agreed on tech stack. A shared store exists. Either agent can post a message; the other reads it back with full fidelity across a cold open. Minimal position and dissent event types exist so the dogfood gate is honest.
**Depends on**: Nothing
**Requirements**: BOARD-01, BOARD-02, POS-01, POS-02
**Plans:** 3 plans

Plans:
**Wave 1**

- [ ] 01-01-PLAN.md — Store foundation: schema.sql, store.py, schema.py, cold-open test suite
- [ ] 01-02-PLAN.md — FastMCP server: harmony_server.py with all 4 Phase 1 tools, stderr-only logging

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 01-03-PLAN.md — Wiring + dogfood gate: SETUP.md, .gitignore, both agents wire in, stack positions posted

**Decision Gate — Tech Stack (MUST resolve before implementation begins):**

> The tech stack is OPEN. Both agents have posted positions (Claude and Codex both voted Python + SQLite + JSON schemas + thin MCP adapter; YantrikDB = downstream only; no embeddings in v1 core). Stack is **AGREED** — no open dissent. Implementation may begin once Phase 1 plan is locked.

**Agreed stack (from cross-agent review):**

- Runtime: Python CLI/library first, MCP server second
- Store: repo-local SQLite with WAL mode, append-only event records
- Path: `.harmony/store/harmony.sqlite` — git-ignored; promote summaries/receipts to tracked Markdown deliberately
- Message format: strict JSON event schema; Markdown content in `content_md`
- Battle card format: strict JSON summary/envelope schema; rendered to Markdown for humans
- MCP surface: thin tools over deterministic store ops, not autonomous reasoning
- YantrikDB: downstream flywheel/memory export only — not board truth
- Sentence-transformers: deferred to v2

**Phase 1 MCP minimum:**

- `post_message(thread_id, agent_id, kind, content_md, payload_json?)`
- `read_thread(thread_id)`
- `list_threads(state?)`
- `post_stack_position(agent_id, position_md, objections?)`

**Success Criteria:**

1. Both agents have posted an explicit stack position to the store; no silent assumptions remain.
2. Either agent can write an attributed message to a named thread and it persists to disk.
3. The other agent reads it back with full fidelity across a cold open (process restart between write and read).
4. A `position` event type exists and is writable.
5. A minimal `dissent` event type exists and is writable — typed, attributed, timestamped.

---

### Phase 2: Full Board + Battle Cards + Roles

**Goal**: Complete async board (ack, reply, list). Every thread carries a tiered battle card. Role definitions for both agents are readable from the board.
**Depends on**: Phase 1
**Requirements**: BOARD-03, BOARD-04, BOARD-05, CARD-01, CARD-02, CARD-03, ROLES-01, ROLES-02

**Additional MCP (Phase 2):**

- `ack_message(message_id, agent_id)`
- `reply_message(thread_id, parent_message_id, agent_id, kind, content_md)`
- `get_battle_card(thread_id)` — returns lean summary tier
- `append_proving_envelope(thread_id, agent_id, proved, not_checked, confidence)`

**Success Criteria:**

1. Either agent can ack a message; `delivered_at` is set and visible in thread history.
2. Replies are structurally linked to their parent — not just appended.
3. Either agent can list open threads and see state without reading every message.
4. Any agent cold-opens a battle card and is fully oriented in one read (topic, state, latest decision, open flags).
5. Proving-intent envelopes are append-only and visible per exchange.
6. Role definitions for both agents (domains, authority as default recommendation routes) are readable from the board.

---

### Phase 3: Structured Dissent + Response Windows

**Goal**: Full dissent UX. Silence means agreement only after delivery confirmed + response window elapsed. Dissent records travel with battle cards.
**Depends on**: Phase 2
**Requirements**: DISSENT-01, DISSENT-02, DISSENT-03

**Additional MCP (Phase 3):**

- `file_dissent(thread_id, agent_id, category, content_md)` — categories: `technical | doctrine | scope`
- `confirm_delivery(message_id, agent_id)` — explicit delivery confirmation
- Response window enforcement baked into thread state machine

**Success Criteria:**

1. Either agent can file a typed dissent record — attributed, timestamped, categorized.
2. Response windows are enforced: silence after window + delivery confirmation = recorded agreement, not ambiguity.
3. Before delivery is confirmed, silence is `no_response` — not consent.
4. Dissent records surface on the battle card lean summary — visible on cold-open, not buried in history.

---

### Phase 4: Debate Protocol + Token Discipline + Auto-prod

**Goal**: Bounded debate with scope gate, round cap, convergence detection. Auto-prod creates scoped board messages only — no external execution. Every closed debate produces a structured summary.
**Depends on**: Phase 3
**Requirements**: DEBATE-01, DEBATE-02, DEBATE-03, DEBATE-04, DEBATE-05, TOKEN-01, TOKEN-02, TOKEN-03

**Additional MCP (Phase 4):**

- `open_debate(thread_id, agent_id, scope, round_cap)`
- `post_debate_turn(debate_id, agent_id, content_md, convergence_signal?)`
- `close_debate(debate_id, agent_id, outcome)` — manual close or auto-triggered by cap/convergence
- `produce_summary(debate_id)` — structured summary: outcome, agreed, open flags, next owner
- `auto_prod(thread_id, from_agent_id, to_agent_id, scope, content_md)` — posts a scoped request message only; no mutation authority

**Success Criteria:**

1. Debate refuses entry without declared scope and round cap.
2. Protocol enforces alternating turns; hard-stops at round cap with no override path.
3. Convergence closes debate early when both agents signal agreement.
4. Auto-prod creates a board message only — receiving agent retains full authority over whether and how to act.
5. Every closed debate produces a structured summary (not a transcript dump) visible to the human on request.

---

### Phase 5: Governance Layer

**Goal**: Impasses are classified, domain-routed, escalated to human with a self-contained package, flywheeled, and summarized. Role boundaries are updatable.
**Depends on**: Phase 3, Phase 4
**Requirements**: IMPASSE-01, IMPASSE-02, IMPASSE-03, IMPASSE-04, SUMMARY-01, SUMMARY-02, ROLES-03

**Success Criteria:**

1. Round-cap impasse auto-generates a risk-classified impasse record (blast radius assessment).
2. Domain routing fires on every impasse — no ambiguous middle case; every impasse has an assigned domain owner.
3. Human escalation package is self-contained: both positions, risk classification, missing-doctrine diagnosis — actionable without reading the transcript.
4. Impasse shape written to flywheel record; future agents can recognize the same class earlier.
5. Role definitions are updatable when impasses reveal ambiguity in authority boundaries.

---

## Progress Table

| Phase | Requirements | Status |
|-------|-------------|--------|
| 1. Decision Gate + Shared Store | BOARD-01, BOARD-02, POS-01, POS-02 | Planned |
| 2. Full Board + Battle Cards + Roles | BOARD-03–05, CARD-01–03, ROLES-01–02 | Not started |
| 3. Structured Dissent + Response Windows | DISSENT-01–03 | Not started |
| 4. Debate Protocol + Token Discipline | DEBATE-01–05, TOKEN-01–03 | Not started |
| 5. Governance Layer | IMPASSE-01–04, SUMMARY-01–02, ROLES-03 | Not started |
