# Requirements — BMG-Harmony v1

## v1 Requirements

### Phase 1 — Decision Gate + Shared Store

- [ ] **BOARD-01**: Any agent can post a message to a named thread with attribution (agent ID, timestamp, content)
- [ ] **BOARD-02**: Any agent can read a thread's full message history
- [ ] **POS-01**: A minimal `position` event type exists — any agent can post a named stack/design position to a thread, attributed and timestamped
- [ ] **POS-02**: A minimal `dissent` event type exists — any agent can file a simple typed objection at Phase 1 level; full dissent UX comes in Phase 3

### Phase 2 — Full Board + Battle Cards + Roles Surface

- [ ] **BOARD-03**: Any agent can acknowledge (ack) a message, marking it received with a `delivered_at` timestamp
- [ ] **BOARD-04**: Any agent can reply to a specific message, preserving thread structure (reply linked to parent, not just appended)
- [ ] **BOARD-05**: Any agent can list open threads and their current state
- [ ] **CARD-01**: Every thread has a lean summary battle card — topic, current state, latest decision, open flags — readable in one cold-open
- [ ] **CARD-02**: Every thread has a proving-intent envelope layer — what each agent claimed to prove, what it didn't check, handoff confidence
- [ ] **CARD-03**: The lean summary is updated at every exchange; envelopes are appended, never overwritten
- [ ] **ROLES-01**: Role definitions for both agents (Claude: supervisor/briefer/reviewer; Codex: executor/builder/Brain 1) are accessible from the board
- [ ] **ROLES-02**: Authority domains are explicit and readable: doctrine/architecture → supervisor as default route; implementation/runtime → executor as default route

### Phase 3 — Structured Dissent + Response Windows

- [ ] **DISSENT-01**: Any agent can file a typed dissent record on any decision or plan — attributed, timestamped, categorized (technical / doctrine / scope)
- [ ] **DISSENT-02**: Silence means agreement *only after* a response window has elapsed AND delivery is confirmed (`delivered_at` set + window expired). Before that, silence is `no_response`, not consent
- [ ] **DISSENT-03**: Dissent records travel with the battle card — they are not buried in message history and are visible on cold-open

### Phase 4 — Debate Protocol + Token Discipline + Auto-prod

- [ ] **DEBATE-01**: Any agent can open a debate on a named topic with a declared scope and round cap — protocol refuses entry without both
- [ ] **DEBATE-02**: The debate protocol enforces alternating turns within the cap
- [ ] **DEBATE-03**: Convergence is detected when both agents mark an exchange as agreed — debate closes early
- [ ] **DEBATE-04**: Either agent can auto-prod the other by posting a scoped request/message to the board — no repo mutation, no git, no external process; receiving agent decides whether and how to act
- [ ] **DEBATE-05**: Every closed debate produces a structured summary: outcome, agreed items, open flags, next owner — full transcript available on request, never the default output
- [ ] **TOKEN-01**: Every debate has a hard round cap — configurable, sensible default (5 rounds)
- [ ] **TOKEN-02**: Convergence detection closes debates early — cap + convergence, whichever first
- [ ] **TOKEN-03**: No debate can open without a declared scope — scope gates entry to the protocol

### Phase 5 — Governance Layer

- [ ] **IMPASSE-01**: When a debate hits its round cap without convergence, the impasse is classified by risk level (blast radius of getting it wrong)
- [ ] **IMPASSE-02**: Domain-routing applied: doctrine/architecture disputes flagged to supervisor; implementation disputes flagged to executor; no ambiguous middle case
- [ ] **IMPASSE-03**: Human escalation package produced: both positions, risk classification, what the impasse reveals about missing doctrine — self-contained and actionable
- [ ] **IMPASSE-04**: Impasse shape encoded to flywheel record — not just resolved, but learned from
- [ ] **SUMMARY-01**: Every closed governance impasse produces a human-visible escalation summary distinct from the debate close summary
- [ ] **SUMMARY-02**: Summary is the default human-facing output — full transcript available on request, not dumped by default
- [ ] **ROLES-03**: Role definitions are updatable — the system learns from impasses and may refine authority boundaries

## v2 (Deferred)

- Real-time simultaneous agent chat (live call-center mode)
- Third-party integrations (Slack, GitHub, etc.)
- More than 2 agents
- GUI or dashboard
- Semantic search / embeddings (sentence-transformers, YantrikDB as board truth)

## Out of Scope (v1)

- User-facing product features — this is infra
- Authentication / access control — trusted internal tools only in v1
- Cross-organization use — BMG-internal only
- YantrikDB as board source of truth — downstream flywheel export only
- Embeddings / semantic search in core store — deterministic coordination first

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| BOARD-01 | Phase 1 | Pending |
| BOARD-02 | Phase 1 | Pending |
| POS-01 | Phase 1 | Pending |
| POS-02 | Phase 1 | Pending |
| BOARD-03 | Phase 2 | Pending |
| BOARD-04 | Phase 2 | Pending |
| BOARD-05 | Phase 2 | Pending |
| CARD-01 | Phase 2 | Pending |
| CARD-02 | Phase 2 | Pending |
| CARD-03 | Phase 2 | Pending |
| ROLES-01 | Phase 2 | Pending |
| ROLES-02 | Phase 2 | Pending |
| DISSENT-01 | Phase 3 | Pending |
| DISSENT-02 | Phase 3 | Pending |
| DISSENT-03 | Phase 3 | Pending |
| DEBATE-01 | Phase 4 | Pending |
| DEBATE-02 | Phase 4 | Pending |
| DEBATE-03 | Phase 4 | Pending |
| DEBATE-04 | Phase 4 | Pending |
| DEBATE-05 | Phase 4 | Pending |
| TOKEN-01 | Phase 4 | Pending |
| TOKEN-02 | Phase 4 | Pending |
| TOKEN-03 | Phase 4 | Pending |
| IMPASSE-01 | Phase 5 | Pending |
| IMPASSE-02 | Phase 5 | Pending |
| IMPASSE-03 | Phase 5 | Pending |
| IMPASSE-04 | Phase 5 | Pending |
| SUMMARY-01 | Phase 5 | Pending |
| SUMMARY-02 | Phase 5 | Pending |
| ROLES-03 | Phase 5 | Pending |
