# Roadmap — BMG-Harmony v1

## Phases

- [ ] **Phase 1: Decision Gate + Shared Store** — Tech stack agreed by both agents; one agent can post, the other can read. Smallest thing that proves the foundation.
- [ ] **Phase 2: Full Message Board + Battle Cards** — Complete async board (ack, reply, list) with per-thread battle cards that survive context death.
- [ ] **Phase 3: Debate Protocol + Token Discipline** — Bounded debate with declared scope, round cap, convergence detection, auto-prod, and structured summary output.
- [ ] **Phase 4: Structured Dissent** — Typed dissent records as a first-class citizen: attributed, categorized, and traveling with the battle card.
- [ ] **Phase 5: Governance Layer** — Impasse classification, domain routing, human escalation, flywheel encoding, human-visible summaries, and surfaced role definitions.

---

## Phase Details

### Phase 1: Decision Gate + Shared Store
**Goal**: Both agents have agreed on the tech stack and proven a shared store works — one agent posts, the other reads.
**Depends on**: Nothing (first phase)
**Requirements**: BOARD-01, BOARD-02

**Decision Gate — Tech Stack (MUST resolve before implementation begins):**

> The tech stack is OPEN. Claude defaults to Python; Codex has implementation authority and may object. Neither agent may begin building until both have explicitly agreed (or one has filed a typed dissent and the disagreement has been resolved). No silent rewrites. This gate is the first act of the protocol eating its own dog food.

**Success Criteria** (what must be TRUE):
  1. Both agents have posted a position on tech stack choice in the shared store; no silent assumptions remain.
  2. One agent (either) can write a message with attribution (agent ID, timestamp, content) to a named thread and the record persists.
  3. The other agent can read that exact message back with full fidelity — no data loss across a cold open.
  4. The store survives process restart — if either agent's context dies and reboots, the post is still there.
**Plans**: TBD

---

### Phase 2: Full Message Board + Battle Cards
**Goal**: Agents can ack, reply, and list threads; every thread carries a lean battle card and proving-intent envelopes.
**Depends on**: Phase 1
**Requirements**: BOARD-03, BOARD-04, BOARD-05, CARD-01, CARD-02, CARD-03

**Success Criteria** (what must be TRUE):
  1. Either agent can acknowledge a message and the ack is recorded and visible in thread history.
  2. Either agent can reply to a specific message and the reply is structurally linked to the parent, not just appended.
  3. Either agent can list all open threads and see their current state without reading every message.
  4. Any agent can cold-open a thread's lean battle card (topic, state, latest decision, open flags) and be oriented in one read — no hunting through message history required.
  5. Proving-intent envelopes exist per exchange (what was claimed proved, what was skipped, handoff confidence); envelopes are appended only, never overwritten.
**Plans**: TBD

---

### Phase 3: Debate Protocol + Token Discipline
**Goal**: Agents can open a bounded debate, take alternating turns, detect convergence, auto-prod each other, and close with a structured summary — never a raw transcript.
**Depends on**: Phase 2
**Requirements**: DEBATE-01, DEBATE-02, DEBATE-03, DEBATE-04, DEBATE-05, TOKEN-01, TOKEN-02, TOKEN-03

**Success Criteria** (what must be TRUE):
  1. A debate cannot be opened without a declared scope and a round cap — the protocol refuses entry without these gates.
  2. The protocol enforces alternating turns and hard-stops when the round cap is reached, with no manual override path.
  3. A debate closes early (before cap) when both agents mark an exchange as agreed — convergence is detected, not assumed.
  4. Either agent can auto-prod the other on a plan within the declared scope without requiring a human relay.
  5. Every closed debate produces a structured summary (outcome, agreed items, open flags, next owner) — the full transcript is available on request but is never the default output.
**Plans**: TBD

---

### Phase 4: Structured Dissent
**Goal**: Any agent can file a typed, attributed dissent record on any decision; silence on a post genuinely means agreement; dissent travels with the battle card.
**Depends on**: Phase 2
**Requirements**: DISSENT-01, DISSENT-02, DISSENT-03

**Success Criteria** (what must be TRUE):
  1. Either agent can file a dissent record against any decision or plan — the record is attributed, timestamped, and categorized (technical / doctrine / scope).
  2. A thread's response window is enforced: after it closes, silence on a post is treated as recorded agreement, not ambiguity.
  3. Dissent records are surfaced on the battle card — they are not buried in message history and are visible on cold-open.
**Plans**: TBD

---

### Phase 5: Governance Layer
**Goal**: Impasses are classified, domain-routed, escalated to the human with a structured package, learned from via the flywheel, and summarized — role definitions are surfaced and updatable.
**Depends on**: Phase 3, Phase 4
**Requirements**: IMPASSE-01, IMPASSE-02, IMPASSE-03, IMPASSE-04, SUMMARY-01, SUMMARY-02, ROLES-01, ROLES-02, ROLES-03

**Success Criteria** (what must be TRUE):
  1. When a debate hits its round cap without convergence, an impasse record is automatically created with a risk classification (blast radius) — not a raw log dump.
  2. Domain routing fires on every impasse: doctrine/architecture disputes are flagged to the supervisor role; implementation disputes are flagged to the executor role — no ambiguous middle case.
  3. The human escalation package contains both agent positions, the risk classification, and an explicit statement of what the impasse reveals about missing doctrine — it is self-contained and actionable without reading the full transcript.
  4. The impasse shape is written to a flywheel record so future agents can recognize the same class of dispute earlier.
  5. Role definitions for both agents (domains, authority boundaries, dissent rules) are readable from the board and are updatable when impasses reveal ambiguity.
**Plans**: TBD

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Decision Gate + Shared Store | 0/? | Not started | - |
| 2. Full Message Board + Battle Cards | 0/? | Not started | - |
| 3. Debate Protocol + Token Discipline | 0/? | Not started | - |
| 4. Structured Dissent | 0/? | Not started | - |
| 5. Governance Layer | 0/? | Not started | - |
