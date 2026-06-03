---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: phase-complete
last_updated: "2026-06-03T13:00:00Z"
progress:
  total_phases: 5
  completed_phases: 1
  total_plans: 3
  completed_plans: 3
  percent: 20
---

# State — BMG-Harmony v1

## Project Reference

**Core value**: Two agents, one coherent team — shared async board, durable battle cards, bounded debate with structured dissent, and a governance loop that learns from impasses.

**Current focus**: Phase 1 — Decision Gate + Shared Store

---

## Current Position

Phase: 01 (decision-gate-shared-store) — COMPLETE
Plan: 3 of 3
**Phase**: 1 — Decision Gate + Shared Store
**Status**: COMPLETE — both agents on board, dogfood gate passed
**Progress**: [##########] 100% Phase 1 done; Phase 2 ready to start

---

## Phase Progress

| Phase | Status | Completed |
|-------|--------|-----------|
| 1. Decision Gate + Shared Store | COMPLETE | 01-01, 01-02, 01-03 |
| 2. Full Message Board + Battle Cards | Not started | - |
| 3. Debate Protocol + Token Discipline | Not started | - |
| 4. Structured Dissent | Not started | - |
| 5. Governance Layer | Not started | - |

---

## Performance Metrics

- Phases complete: 0/5
- Requirements delivered: 4/28 (BOARD-01, BOARD-02, POS-01, POS-02 — delivered in 01-01/01-02; wiring done in 01-03)
- Phases with plans: 1/5

| Phase | Plan | Duration | Tasks | Files |
|-------|------|----------|-------|-------|
| 01 | 01 | 15min | 2 | 9 |
| 01 | 02 | 15min | 1 | 1 |
| 01 | 03 | 20min | 2 auto + 2 checkpoints | 4 |

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
| Tech stack | Python + SQLite WAL + JSONSchema + uuid_utils (uuid7) + FastMCP. Both agents agreed. | LOCKED |
| ToolError import path | mcp.server.fastmcp.exceptions.ToolError (not mcp.server.fastmcp.ToolError — that path does not exist in 1.27.x) | Locked |
| revision = last_insert_rowid() | Monotonically increasing per table; no extra query; debuggable | Locked |
| Thread auto-create via INSERT OR IGNORE | Idempotent; handles concurrent first-posts without race | Locked |
| .gitignore uses glob .harmony/store/* | Allows .gitkeep to be tracked via negation rule (!.harmony/store/.gitkeep) | Locked |
| bmg-harmony in project-scope .mcp.json | Added to .codex/.mcp.json (project scope); user-scope requires CLI (documented in SETUP.md) | Locked |
| Claude stack position posted via store layer | Executor agent lacks active MCP session; wrote directly via write_event(); identical data | Locked |

### Open Questions

- None — tech stack gate resolved; all Phase 1 plan 01-01 questions answered

### Blockers

- None

### Todos

- Start Phase 2: Full Message Board + Battle Cards (`$gsd-execute-phase 2`)

---

## Session Continuity

**Last updated**: 2026-06-03T13:00:00Z
**Stopped at**: Phase 1 complete — both agents on board, dogfood gate passed (harmony-stack-decision: 2 events, claude + codex). SETUP.md corrected (config path + PYTHONPATH). Claude Code restart required to load updated .mcp.json.
**Next action**: Restart Claude Code → verify bmg-harmony in tool list → start Phase 2
