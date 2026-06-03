---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: checkpoint-pending
last_updated: "2026-06-03T12:15:00Z"
progress:
  total_phases: 5
  completed_phases: 0
  total_plans: 3
  completed_plans: 2
  percent: 33
---

# State — BMG-Harmony v1

## Project Reference

**Core value**: Two agents, one coherent team — shared async board, durable battle cards, bounded debate with structured dissent, and a governance loop that learns from impasses.

**Current focus**: Phase 1 — Decision Gate + Shared Store

---

## Current Position

Phase: 01 (decision-gate-shared-store) — CHECKPOINT PENDING
Plan: 3 of 3 (auto-tasks complete; awaiting human verification + Codex dogfood)
**Phase**: 1 — Decision Gate + Shared Store
**Plan**: 01-03 auto-tasks COMPLETE — awaiting checkpoints 3 and 4
**Status**: Checkpoint pending (human-verify: Claude wiring + Codex dogfood gate)
**Progress**: [#####-----] 33% (2.5/3 plans — 01-03 auto-tasks done, checkpoints pending)

---

## Phase Progress

| Phase | Status | Completed |
|-------|--------|-----------|
| 1. Decision Gate + Shared Store | Checkpoint pending (01-03 auto-tasks done) | 01-01, 01-02, 01-03 (partial) |
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

- Human: run `claude mcp list` to verify bmg-harmony is visible (Task 3 checkpoint)
- Codex: add [mcp_servers.bmg-harmony] to config.toml per SETUP.md Section 4
- Codex: call post_stack_position in its session (Task 4 dogfood gate)
- After dogfood gate passes: run full pytest suite (8 tests), confirm DOGFOOD GATE: PASSED

---

## Session Continuity

**Last updated**: 2026-06-03T12:15:00Z
**Stopped at**: 01-03 auto-tasks complete — awaiting Task 3 (Claude wiring verification) and Task 4 (Codex dogfood gate)
**Next action**: Human: `claude mcp list` to verify bmg-harmony | Codex: wire config.toml + post_stack_position
