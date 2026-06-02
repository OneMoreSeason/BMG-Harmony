# State — BMG-Harmony v1

## Project Reference

**Core value**: Two agents, one coherent team — shared async board, durable battle cards, bounded debate with structured dissent, and a governance loop that learns from impasses.

**Current focus**: Phase 1 — Decision Gate + Shared Store

---

## Current Position

**Phase**: 1 — Decision Gate + Shared Store
**Plan**: None yet (planning not started)
**Status**: Not started
**Progress**: [----------] 0%

---

## Phase Progress

| Phase | Status | Completed |
|-------|--------|-----------|
| 1. Decision Gate + Shared Store | Not started | - |
| 2. Full Message Board + Battle Cards | Not started | - |
| 3. Debate Protocol + Token Discipline | Not started | - |
| 4. Structured Dissent | Not started | - |
| 5. Governance Layer | Not started | - |

---

## Performance Metrics

- Phases complete: 0/5
- Requirements delivered: 0/28
- Phases with plans: 0/5

---

## Accumulated Context

### Key Decisions

| Decision | Rationale | Status |
|----------|-----------|--------|
| Async-first architecture | Survives context death; naturally token-bounded | Locked |
| Neutral repo (neither brain owns it) | Both agents are equal peers | Locked |
| Tiered battle cards | Cold-open from summary; deep audit from envelopes | Locked |
| Cap + convergence stop rule | Bounded by round limit AND convergence detection | Locked |
| Structured dissent as first-class | Silence = agreement; typed record required for objection | Locked |
| Human tiebreaker with flywheel | Impasses escalate AND encode a learning note | Locked |
| Tech stack | Claude defaults Python; Codex has implementation authority and may object. Both must agree explicitly. | OPEN — Phase 1 gate |

### Open Questions

- Tech stack: Python, Node, or other? Requires explicit agreement from both Claude and Codex before Phase 1 implementation begins.

### Blockers

- None yet

### Todos

- Plan Phase 1 after tech stack decision gate is resolved

---

## Session Continuity

**Last updated**: 2026-06-02
**Next action**: Run `/gsd:plan-phase 1` — but note: Phase 1 begins with the tech stack decision gate. Both agents must post a position and reach explicit agreement before any implementation plan is written.
