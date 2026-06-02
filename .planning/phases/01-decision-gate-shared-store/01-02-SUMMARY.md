---
phase: 01-decision-gate-shared-store
plan: "02"
subsystem: api
tags: [fastmcp, mcp, sqlite, python, stdio-transport]

# Dependency graph
requires:
  - phase: 01-01
    provides: store.py — init_db, write_event, read_thread, list_threads + schema.py validate_event
provides:
  - FastMCP server entrypoint (harmony_server.py) with all 4 Phase 1 MCP tools
  - post_message, read_thread, list_threads, post_stack_position tools over stdio transport
  - stderr-only logging — stdout owned by MCP JSON-RPC wire protocol
  - HARMONY_DB_PATH env-driven db path; RuntimeError raised at lifespan start if unset
affects: [01-03-PLAN, agent-wiring, dogfood-gate]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "FastMCP lifespan pattern: asynccontextmanager opens/closes SQLite once per process"
    - "Module-level _db variable shared across tool functions (FastMCP serializes calls)"
    - "ToolError imported from mcp.server.fastmcp.exceptions (verified path for mcp 1.27.x)"
    - "All logging via logging.basicConfig(stream=sys.stderr) — never stdout"

key-files:
  created:
    - server/harmony_server.py
  modified: []

key-decisions:
  - "ToolError import path: mcp.server.fastmcp.exceptions.ToolError (not fastmcp.exceptions — verified at implementation time)"
  - "Module-level _db variable over Context injection — simpler, FastMCP serializes tool calls so no threading issue"
  - "post_stack_position posts to harmony-stack-decision with kind=position per D-17"

patterns-established:
  - "FastMCP lifespan: open db in asynccontextmanager, yield context dict, close in finally block"
  - "Tool functions return dict directly; store layer raises ToolError on validation/integrity errors"
  - "Logging setup as first module-level code before any other imports"

requirements-completed: [BOARD-01, BOARD-02, POS-01, POS-02]

# Metrics
duration: 15min
completed: 2026-06-02
---

# Phase 1 Plan 02: harmony_server.py Summary

**FastMCP server with 4 MCP tools (post_message, read_thread, list_threads, post_stack_position) over stdio transport, stderr-only logging, and HARMONY_DB_PATH-driven SQLite connection**

## Performance

- **Duration:** 15 min
- **Started:** 2026-06-02T22:30:00Z
- **Completed:** 2026-06-02T22:45:00Z
- **Tasks:** 1 implemented (Task 2 is a human-verify checkpoint)
- **Files modified:** 1

## Accomplishments

- `server/harmony_server.py` created with all 4 Phase 1 MCP tools
- `logging.basicConfig(stream=sys.stderr)` is the first call — zero stdout writes confirmed
- ToolError import path verified: `mcp.server.fastmcp.exceptions.ToolError` (mcp 1.27.x)
- `post_stack_position` posts to `harmony-stack-decision` with `kind=position` per D-17
- `HARMONY_DB_PATH` drives db path; `RuntimeError` raised at lifespan start if unset

## Task Commits

1. **Task 1: harmony_server.py — FastMCP server with all 4 tools** — `96d01b9` (feat)

**Plan metadata:** (pending final metadata commit)

## Files Created/Modified

- `server/harmony_server.py` — FastMCP server entrypoint: lifespan, 4 @mcp.tool() functions, stderr logging, env-driven db path

## Decisions Made

- **ToolError import path:** Used `from mcp.server.fastmcp.exceptions import ToolError` — confirmed working on mcp 1.27.x. The plan listed `fastmcp.exceptions` first; the critical deviation note from plan 01-01 specified the correct path, which was verified before writing.
- **Module-level `_db` over Context injection:** Plan specified both options; module-level `_db` is simpler and correct since FastMCP serializes tool calls in Phase 1 load.
- **`post_stack_position` with `json.dumps({"objections": ...})`:** Stores objections as JSON string in `payload_json` per plan spec.

## Deviations from Plan

### Applied Critical Deviation from Plan 01-01

**[Rule 1 - Bug Prevention] ToolError import path corrected before implementation**
- **Source:** `<critical_deviation_from_prior_plan>` in execution prompt
- **Issue:** Plan 01-02 listed `fastmcp.exceptions.ToolError` as primary attempt; mcp 1.27.x ships this at `mcp.server.fastmcp.exceptions`
- **Fix:** Used `from mcp.server.fastmcp.exceptions import ToolError` directly — no fallback chain needed
- **Verification:** Import probe confirmed `ToolError from mcp.server.fastmcp.exceptions: OK` before writing
- **Committed in:** `96d01b9` (Task 1 commit)

---

**Total deviations:** 1 (applied known fix from prior plan — no scope creep)
**Impact on plan:** Necessary correctness fix. Import probe confirmed before writing.

## Issues Encountered

None — all verification checks passed on first attempt.

## Threat Surface Scan

No new threat surface beyond what is documented in the plan's threat model (T-02-01 through T-02-SC).

- T-02-01 (stdout pollution): Mitigated — `logging.basicConfig(stream=sys.stderr)` at module top, zero `print()` calls confirmed via AST analysis
- T-02-02 (kind field validation): Mitigated by store layer `validate_event()` enforcing kind enum
- T-02-04 (payload_json): Low risk accepted per plan; `json.dumps()` used for `post_stack_position` payload

## Known Stubs

None — all 4 tools are fully wired to the store layer. No placeholder data.

## Next Phase Readiness

- `harmony_server.py` is ready for agent wiring (Plan 01-03: SETUP.md + .gitignore + dogfood gate)
- Both agents can register `bmg-harmony` in their MCP config and call all 4 tools
- `HARMONY_DB_PATH` must be set to the absolute path of `.harmony/store/harmony.sqlite` in agent configs

---
*Phase: 01-decision-gate-shared-store*
*Completed: 2026-06-02*
