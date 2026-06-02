---
phase: 01-decision-gate-shared-store
plan: "01"
subsystem: database
tags: [sqlite, jsonschema, uuid_utils, pytest, wal, append-only, event-store]

# Dependency graph
requires: []
provides:
  - "server/schema.sql: canonical DDL with threads + events tables and append-only triggers"
  - "server/schema.py: EVENT_SCHEMA Draft7 dict + compiled validator + validate_event()"
  - "server/store.py: init_db, write_event, read_thread, list_threads with WAL mode"
  - "tests/: 8-test pytest suite proving correctness + cold-open durability"
  - ".harmony/store/.gitkeep: directory placeholder for the runtime SQLite store"
affects: [02-harmony-server, 03-gitignore-and-setup]

# Tech tracking
tech-stack:
  added: [sqlite3 (stdlib), jsonschema Draft7Validator, uuid_utils (uuid7), pytest]
  patterns:
    - "Append-only event log enforced at DB layer via BEFORE UPDATE/DELETE triggers raising RAISE(ABORT)"
    - "ToolError fallback: try-import mcp.server.fastmcp.exceptions.ToolError; local Exception subclass if unavailable"
    - "validate_event called before every INSERT; hard reject — no warn-and-store"
    - "Thread auto-creation via INSERT OR IGNORE for idempotent concurrent first-posts"
    - "cold-open proof: explicit con.close() before opening con2 — not GC-reliant"

key-files:
  created:
    - server/__init__.py
    - server/schema.sql
    - server/schema.py
    - server/store.py
    - tests/__init__.py
    - tests/conftest.py
    - tests/test_store.py
    - tests/test_cold_open.py
    - .harmony/store/.gitkeep
  modified: []

key-decisions:
  - "ToolError import: mcp.server.fastmcp.exceptions.ToolError (not mcp.server.fastmcp.ToolError — that import path does not exist in mcp 1.27.x)"
  - "PRAGMA statements in schema.sql are executed via executescript(); they are idempotent and harmless on re-run"
  - "revision = last_insert_rowid() cast to int — monotonically increasing per table, no extra query needed"
  - "event_id and timestamp auto-generated in write_event if not supplied by caller (callers may supply for testability)"

patterns-established:
  - "Pattern: parameterized queries (? placeholders) for all user-supplied values — no string formatting into SQL"
  - "Pattern: read schema.sql via __file__-relative path in init_db() so tests and server both find it correctly"
  - "Pattern: tmp_db fixture yields open connection; teardown calls con.close() explicitly"

requirements-completed: [BOARD-01, BOARD-02, POS-01, POS-02]

# Metrics
duration: 15min
completed: 2026-06-02
---

# Phase 1 Plan 01: SQLite Store Layer Summary

**Append-only SQLite event store with WAL mode, JSONSchema validation, and a full 8-test pytest suite including cold-open durability proof**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-06-02T22:16:00Z
- **Completed:** 2026-06-02T22:20:26Z
- **Tasks:** 2
- **Files modified:** 9 created

## Accomplishments

- SQLite schema DDL committed to git as canonical source (schema.sql): threads + events tables, two append-only triggers enforcing immutability at the DB layer
- EVENT_SCHEMA Draft7 validator in schema.py: hard-rejects missing fields, empty strings, invalid kind values, extra properties
- Full store API in store.py: init_db (WAL, executescript DDL), write_event (uuid7 id generation, validate_event gate, INSERT OR IGNORE thread auto-create, IntegrityError -> ToolError), read_thread (ordered by rowid), list_threads (optional state filter)
- 8 pytest tests all green: write receipt shape, invalid rejection with no row written, read ordering, append-only IntegrityError (not OperationalError), position kind, dissent kind, list_threads filter, and cold-open durability proof with two separate connections

## Task Commits

1. **Task 1: Schema DDL and validation module** - `1844fb0` (feat)
2. **Task 2: Store layer and full test suite** - `d35a80a` (feat)

## Files Created/Modified

- `server/__init__.py` - Empty package marker enabling test imports
- `server/schema.sql` - Canonical DDL: threads table, events table, prevent_event_update trigger, prevent_event_delete trigger, WAL + synchronous=NORMAL PRAGMAs
- `server/schema.py` - EVENT_SCHEMA dict + compiled Draft7Validator + validate_event() raising jsonschema.ValidationError
- `server/store.py` - init_db, write_event, read_thread, list_threads; ToolError fallback for mcp-less imports
- `tests/__init__.py` - Empty package marker
- `tests/conftest.py` - tmp_db fixture (init_db + teardown close)
- `tests/test_store.py` - 7 unit tests covering all store behaviors
- `tests/test_cold_open.py` - Cold-open proof: write con1.close() then raw sqlite3.connect() for con2
- `.harmony/store/.gitkeep` - Directory placeholder; harmony.sqlite will be git-ignored in Plan 03

## Decisions Made

- **ToolError import path corrected:** Research noted `mcp.server.fastmcp.ToolError` but that path does not exist in mcp 1.27.x. The correct path is `mcp.server.fastmcp.exceptions.ToolError`. Used with try/except fallback so store.py works without MCP installed.
- **PRAGMA in schema.sql via executescript:** executescript() handles PRAGMA statements correctly; they are idempotent and safe to re-run on existing databases.
- **revision = last_insert_rowid():** Selected over event-count-in-thread approach — simpler, monotonically increasing, no extra query, debuggable.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Corrected ToolError import path**
- **Found during:** Task 2 (store.py implementation)
- **Issue:** Research doc (Assumption A3) flagged `fastmcp.exceptions.ToolError` as the path but noted it needed verification. Live test confirmed `from mcp.server.fastmcp import ToolError` raises ImportError in mcp 1.27.x; correct path is `mcp.server.fastmcp.exceptions`.
- **Fix:** Used `from mcp.server.fastmcp.exceptions import ToolError` wrapped in try/except with local fallback class.
- **Files modified:** server/store.py
- **Verification:** `python -c "from mcp.server.fastmcp.exceptions import ToolError; print('OK')"` succeeds; all 8 tests pass.
- **Committed in:** d35a80a (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 3 - blocking import)
**Impact on plan:** Import path correction was necessary for correctness. No scope change.

## Issues Encountered

None beyond the ToolError import path deviation documented above.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes beyond what the threat model covers. T-01-01, T-01-02, T-01-03 mitigations are all in place:
- All SQLite queries use ? parameterized placeholders (T-01-01)
- payload_json validated as string-or-null by jsonschema (T-01-02)
- BEFORE UPDATE/DELETE triggers with RAISE(ABORT) confirmed raising sqlite3.IntegrityError (T-01-03)

## Next Phase Readiness

- store.py API is stable and matches the exact interface contracts specified in the plan's `<interfaces>` block
- Plan 02 (harmony_server.py) can import `init_db, write_event, read_thread, list_threads` from `server.store` immediately
- Plan 02 can import `validate_event, EVENT_SCHEMA` from `server.schema` immediately
- .harmony/store/ directory exists; .gitignore entry for harmony.sqlite is deferred to Plan 03

## Self-Check: PASSED

- server/schema.sql: EXISTS
- server/schema.py: EXISTS
- server/store.py: EXISTS
- tests/test_store.py: EXISTS
- tests/test_cold_open.py: EXISTS
- .harmony/store/.gitkeep: EXISTS
- Commit 1844fb0: EXISTS (feat(01-01): schema DDL and validation module)
- Commit d35a80a: EXISTS (feat(01-01): store layer and full test suite)
- pytest: 8/8 PASSED

---
*Phase: 01-decision-gate-shared-store*
*Completed: 2026-06-02*
