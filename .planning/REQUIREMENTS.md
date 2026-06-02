# Requirements — BMG-Harmony v1

## v1 Requirements

### Foundation

- [ ] **BOARD-01**: Any agent can post a message to a named thread with attribution (agent ID, timestamp, content)
- [ ] **BOARD-02**: Any agent can read a thread's full message history
- [ ] **BOARD-03**: Any agent can acknowledge (ack) a message, marking it received
- [ ] **BOARD-04**: Any agent can reply to a specific message, preserving thread structure
- [ ] **BOARD-05**: Any agent can list open threads and their current state

- [ ] **CARD-01**: Every thread has a lean summary battle card — topic, current state, latest decision, open flags — readable in one cold-open
- [ ] **CARD-02**: Every thread has a proving-intent envelope layer — what each agent claimed to prove, what it didn't check, handoff confidence
- [ ] **CARD-03**: The lean summary is updated at every exchange; envelopes are appended, never overwritten

- [ ] **DEBATE-01**: Any agent can open a debate on a named topic with a declared scope and round cap
- [ ] **DEBATE-02**: The debate protocol enforces alternating turns within the cap
- [ ] **DEBATE-03**: Convergence is detected when both agents mark an exchange as agreed — debate closes early
- [ ] **DEBATE-04**: Either agent can auto-prod the other on a plan within a declared scope (no human relay required)
- [ ] **DEBATE-05**: Debate ends in a structured summary: outcome, what was agreed, what wasn't, open flags — not a raw transcript

- [ ] **DISSENT-01**: Any agent can file a typed dissent record on any decision or plan — attributed, timestamped, categorized (technical / doctrine / scope)
- [ ] **DISSENT-02**: Silence on a post within a thread's response window means genuine agreement — dissent is the explicit act, not agreement
- [ ] **DISSENT-03**: Dissent records travel with the battle card — they are not buried in message history

### Governance

- [ ] **IMPASSE-01**: When a debate hits its round cap without convergence, the impasse is classified by risk level (blast radius of getting it wrong)
- [ ] **IMPASSE-02**: Domain-routing applied: doctrine/architecture disputes flagged to supervisor role; implementation disputes flagged to executor role
- [ ] **IMPASSE-03**: Human escalation package produced: both positions, risk classification, what the impasse reveals about missing doctrine
- [ ] **IMPASSE-04**: Impasse shape encoded to flywheel — not just resolved, but learned from

- [ ] **SUMMARY-01**: Every closed debate produces a human-visible summary: outcome, agreed items, disagreements, open flags, next owner
- [ ] **SUMMARY-02**: Summary is the default human-facing output — full transcript available on request, not dumped by default

- [ ] **ROLES-01**: Role definitions for both agents (Claude: supervisor/briefer/reviewer; Codex: executor/builder/Brain 1) are accessible from the board
- [ ] **ROLES-02**: Authority domains are explicit: doctrine/architecture → supervisor; implementation/runtime → executor
- [ ] **ROLES-03**: Role definitions are updatable — the system learns from impasses and may refine authority boundaries

- [ ] **TOKEN-01**: Every debate has a hard round cap — configurable, with a sensible default (e.g. 5 rounds)
- [ ] **TOKEN-02**: Convergence detection closes debates early — cap + convergence, whichever first
- [ ] **TOKEN-03**: No debate can run without a declared scope — scope gates entry to the protocol

## v2 (Deferred)

- Real-time simultaneous agent chat (live call-center mode)
- Third-party integrations (Slack, GitHub, etc.)
- More than 2 agents
- GUI or dashboard

## Out of Scope (v1)

- User-facing product features — this is infra
- Authentication / access control — trusted internal tools only in v1
- Cross-organization use — BMG-internal only

## Traceability

*Populated by roadmapper.*
