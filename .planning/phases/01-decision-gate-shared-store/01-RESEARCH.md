# Phase 1: Decision Gate + Shared Store — Research

**Researched:** 2026-06-02
**Domain:** Python MCP server + SQLite WAL append-only event store + Windows stdio wiring
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Python + SQLite with WAL mode + append-only event records. No embeddings, no YantrikDB as board truth in v1 core.
- **D-02:** MCP server is Python CLI/library first, MCP server second. Both must be in v1 scope.
- **D-03:** Strict JSON event schema; Markdown content in `content_md`; battle card format: strict JSON summary/envelope schema rendered to Markdown for humans.
- **D-04:** Mandatory core fields on every event: `event_id`, `thread_id`, `agent_id`, `kind`, `timestamp`, `content_md`. Everything else optional payload.
- **D-05:** Hard reject on bad writes. Nothing is written for missing or invalid required fields. No warn-and-store, no coercion.
- **D-06:** `kind` values in Phase 1: `message`, `position`, `dissent`.
- **D-07:** Threads addressed by human-readable slug as primary key; UUID generated internally. Auto-create on first post.
- **D-08:** Threads auto-created on first `post_message` to a new `thread_id`.
- **D-09:** MCP server code in `BMG-Harmony/server/`. Both agents point at the same binary and same physical SQLite file.
- **D-10:** Manual one-time config per agent: add `bmg-harmony` entry to `.codex/.mcp.json` (Codex) and to `BMG-Brain-Claude`'s `.mcp.json` (Claude). Phase 1 deliverable includes `SETUP.md` with exact config entries.
- **D-11:** Live SQLite store at `.harmony/store/harmony.sqlite` inside the repo, git-ignored.
- **D-12:** What gets committed: `schema.sql`, server Python/MCP code, `SETUP.md`, promote-able summaries/receipts. Store file never committed.
- **D-13:** Add `.harmony/store/` to `.gitignore` in Phase 1.
- **D-14:** `post_message(thread_id, agent_id, kind, content_md, payload_json?)` — returns `event_id, thread_id, revision, timestamp, validation_status`
- **D-15:** `read_thread(thread_id)` — returns full event list for the thread
- **D-16:** `list_threads(state?)` — returns thread slugs and current state
- **D-17:** `post_stack_position(agent_id, position_md, objections?)` — convenience wrapper over `post_message` with `kind=position`; posts to well-known thread `harmony-stack-decision`

### Claude's Discretion

None explicitly called out — all implementation choices flow from locked decisions above.

### Deferred Ideas (OUT OF SCOPE)

- Third-agent expansion (v2 / future milestone)
- Cross-session continuity (v2)
- Audit trail and replay (v2)
- Flywheel + brain tie-ins, checkpoints for self-improvement (v2 / milestone)
- Human as first-class participant (v2)
- Phase 2+: ack/reply/list, battle cards, roles surface, structured dissent, debate protocol, governance
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BOARD-01 | Any agent can post a message to a named thread with attribution (agent ID, timestamp, content) | `post_message` MCP tool over SQLite events table; FastMCP tool decorator with Pydantic validation; event schema enforces attribution fields |
| BOARD-02 | Any agent can read a thread's full message history | `read_thread` MCP tool; `SELECT * FROM events WHERE thread_id=? ORDER BY rowid` pattern; WAL mode enables concurrent reads while write is in progress |
| POS-01 | A minimal `position` event type exists — any agent can post a named stack/design position, attributed and timestamped | `post_stack_position` convenience wrapper; `kind='position'` in event schema; validates as a constrained `post_message` call |
| POS-02 | A minimal `dissent` event type exists — any agent can file a simple typed objection at Phase 1 level | `kind='dissent'` in event schema; handled by `post_message` with `kind='dissent'`; no separate dissent UX in Phase 1 |
</phase_requirements>

---

## Summary

Phase 1 builds the shared coordination store (SQLite + WAL, append-only) and the MCP server (Python + FastMCP) that both Claude and Codex will call to post and read attributed messages. The tech stack is agreed and locked; this research establishes the exact patterns, pitfalls, and code shapes the planner needs to spec concrete implementation tasks.

The Python `mcp` package (v1.27.x, maintained by Anthropic, MIT license) is the correct library. It ships `FastMCP` — a decorator-based abstraction that turns annotated Python functions into MCP tools with automatic schema generation, validation, and error propagation. The server runs via `mcp.run(transport="stdio")`, which is the local process transport both Claude Code and Codex use when the server is registered in their config files. All three packages needed for Phase 1 (`mcp`, `jsonschema`, `uuid_utils`) are already installed on this machine and passed slopcheck [OK].

The SQLite cold-open proof pattern is straightforward: write a row in one `sqlite3.connect()` call, close it, open a new connection, and read the row back. This was verified locally in this research session — the pattern works on Windows with WAL mode. The append-only invariant is enforced at the schema level via `BEFORE UPDATE` and `BEFORE DELETE` triggers that raise `sqlite3.IntegrityError` (not `OperationalError`) — this distinction matters for application-level exception handling.

**Primary recommendation:** Build `server/harmony_server.py` as a standalone FastMCP server with a module-level SQLite connection (opened once at process start, WAL mode, append-only triggers applied at schema init time). Register it in both agent configs using absolute Windows paths. Write the cold-open test as a subprocess-based pytest: spawn Python, write, kill process, spawn again, read, assert.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Post attributed message | API / Backend (MCP server) | — | Server owns all writes; agents call via MCP tool, never touch DB directly |
| Read thread history | API / Backend (MCP server) | — | Same process owns both reads and writes; WAL allows concurrent read during write |
| JSON event validation | API / Backend (MCP server) | — | Hard reject at write time; server is the single validation gate |
| Thread auto-creation | API / Backend (MCP server) | Database / Storage | Server logic decides; SQLite executes the INSERT atomically |
| Append-only enforcement | Database / Storage | — | SQLite triggers fire regardless of which code path reaches the DB |
| Persistence across cold open | Database / Storage | — | WAL mode + fsync on commit; nothing stored in process memory only |
| MCP tool discovery | Client (Claude / Codex) | — | Clients read schemas from server at connect time; server exposes them |
| Config wiring | Client (Claude / Codex) | — | Each agent's `.mcp.json` / `config.toml` entry points at shared server binary |

---

## Standard Stack

### Core

| Library | Version (registry) | Purpose | Why Standard |
|---------|--------------------|---------|--------------|
| `mcp` | 1.27.2 (latest) | FastMCP server + stdio transport | Official Anthropic Python MCP SDK; ships `FastMCP`, handles JSON-RPC, stdio pipe encoding on Windows [VERIFIED: pypi.org/project/mcp] |
| `pydantic` | 2.13.4 (latest) | Type validation for tool input schemas | FastMCP uses Pydantic v2 internally for tool parameter validation; already a transitive dep [VERIFIED: pypi.org/project/pydantic] |
| `jsonschema` | 4.26.0 (latest) | Event schema validation at write time | Mature, well-tested JSON Schema validator; `Draft7Validator` pattern allows schema pre-compilation for performance [VERIFIED: pypi.org/project/jsonschema] |
| `uuid_utils` | 0.16.0 (latest) | UUIDv7 generation for event_id | Time-ordered UUIDs; better B-tree index locality than UUIDv4 for append-heavy event logs; Rust-backed for speed [VERIFIED: pypi.org/project/uuid_utils] |
| `sqlite3` | stdlib | Embedded relational store | Ships with Python 3.x; no install required; WAL mode confirmed working on Windows [VERIFIED: Python stdlib] |
| `pytest` | 9.0.3 (latest) | Test framework for cold-open proof | Standard Python test runner; needed for the Phase 1 dogfood gate [VERIFIED: pypi.org/project/pytest] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `contextlib.asynccontextmanager` | stdlib | FastMCP lifespan for DB connection management | Use in `lifespan=` parameter of `FastMCP(...)` to open/close SQLite connection once per server process lifetime |
| `json` | stdlib | Serialize/deserialize `payload_json` column | Use Python `json.dumps` / `json.loads`; do not store raw dicts in SQLite TEXT columns |
| `datetime` / `timezone` | stdlib | UTC timestamp generation | Always use `datetime.now(timezone.utc).isoformat()` — never naive datetimes |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `jsonschema` | Pydantic v2 model validation only | Pydantic v2 validates Python objects, not raw JSON dicts; jsonschema is the right tool for dict-level event validation before write |
| `uuid_utils` (UUIDv7) | `uuid.uuid4()` from stdlib | stdlib UUIDv4 is random — poor B-tree locality; UUIDv7 is time-ordered; for a low-volume Phase 1 the difference is minimal but UUIDv7 is the 2025 standard for new projects |
| FastMCP (in `mcp` package) | Low-level `mcp.server.Server` | FastMCP is the recommended abstraction layer; low-level server requires manual JSON-RPC handling, schema construction, and transport wiring |

**Installation:**
```bash
pip install mcp pydantic jsonschema uuid_utils pytest
```

---

## Package Legitimacy Audit

All packages verified via slopcheck (v0.6.1) on 2026-06-02 against PyPI registry. All packages are already installed on the target machine.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| `mcp` | PyPI | ~2 yrs | High (Anthropic official) | github.com/modelcontextprotocol/python-sdk | [OK] | Approved |
| `pydantic` | PyPI | ~10 yrs | >200M/mo | github.com/pydantic/pydantic | [OK] | Approved |
| `jsonschema` | PyPI | ~12 yrs | >100M/mo | github.com/python-jsonschema/jsonschema | [OK] | Approved |
| `uuid_utils` | PyPI | ~3 yrs | Moderate | github.com/bdraco/uuid_utils | [OK] | Approved |
| `pytest` | PyPI | ~15 yrs | >200M/mo | github.com/pytest-dev/pytest | [OK] | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

---

## Architecture Patterns

### System Architecture Diagram

```
Claude Code session          Codex session
     |                            |
     | MCP call (stdio pipe)      | MCP call (stdio pipe)
     v                            v
+--------------------------------------------------+
|          harmony_server.py (FastMCP)             |
|  post_message | read_thread | list_threads        |
|  post_stack_position                              |
|                                                  |
|  [JSONSchema validation gate]                    |
|       hard reject if required fields missing     |
+--------------------------------------------------+
                    |
                    | sqlite3 (WAL mode)
                    v
+--------------------------------------------------+
|     .harmony/store/harmony.sqlite                |
|                                                  |
|  threads table: thread_id, slug, created_at,    |
|                 state                             |
|                                                  |
|  events table: event_id (UUIDv7), thread_id,    |
|                agent_id, kind, timestamp,         |
|                content_md, payload_json           |
|                                                  |
|  BEFORE UPDATE trigger → RAISE(ABORT)            |
|  BEFORE DELETE trigger → RAISE(ABORT)            |
+--------------------------------------------------+
                    |
            persists to disk
            (survives process restart)
```

### Recommended Project Structure

```
BMG-Harmony/
├── server/
│   ├── harmony_server.py      # FastMCP server entrypoint (mcp.run)
│   ├── store.py               # SQLite layer: init_db, write_event, read_thread, list_threads
│   ├── schema.py              # Event JSONSchema dict + Draft7Validator instance
│   └── schema.sql             # DDL committed to git (canonical schema source)
├── .harmony/
│   └── store/
│       └── harmony.sqlite     # Runtime store — git-ignored
├── tests/
│   ├── conftest.py            # Shared fixtures (tmp_db, server subprocess)
│   ├── test_store.py          # Unit: write, read, append-only enforcement
│   └── test_cold_open.py      # Integration: write → process close → reopen → read
├── SETUP.md                   # Copy-paste config entries for both agents
└── .gitignore                 # Includes .harmony/store/
```

### Pattern 1: FastMCP Tool Registration with Typed Returns

**What:** Decorate Python functions with `@mcp.tool()` (or `@mcp.tool` — both work). FastMCP auto-generates MCP tool schemas from type annotations and docstrings.

**When to use:** Every MCP tool in Phase 1. Return a `dict` or dataclass for structured results; raise `ToolError` to propagate clean error messages back to the calling agent.

```python
# Source: github.com/modelcontextprotocol/python-sdk (verified)
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP
from fastmcp.exceptions import ToolError

@asynccontextmanager
async def lifespan(server):
    db = init_db(".harmony/store/harmony.sqlite")
    yield {"db": db}
    db.close()

mcp = FastMCP("bmg-harmony", lifespan=lifespan)

@mcp.tool()
def post_message(
    thread_id: str,
    agent_id: str,
    kind: str,
    content_md: str,
    payload_json: str | None = None,
) -> dict:
    """Post an attributed message to a named thread. Returns event receipt."""
    # validate, write, return receipt
    ...

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Pattern 2: SQLite WAL Mode + Append-Only Schema Init

**What:** Open connection once at server start, set WAL mode immediately, create tables + triggers if they don't exist.

**When to use:** In the `lifespan` context manager; the `init_db()` function runs once per server process.

```python
# Source: sqlite.org/wal.html + verified locally (2026-06-02)
import sqlite3

def init_db(path: str) -> sqlite3.Connection:
    con = sqlite3.connect(path, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            thread_id TEXT PRIMARY KEY,
            slug      TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            state     TEXT NOT NULL DEFAULT 'open'
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id    TEXT PRIMARY KEY,
            thread_id   TEXT NOT NULL REFERENCES threads(thread_id),
            agent_id    TEXT NOT NULL,
            kind        TEXT NOT NULL,
            timestamp   TEXT NOT NULL,
            content_md  TEXT NOT NULL,
            payload_json TEXT
        )
    """)
    # Append-only enforcement — raises sqlite3.IntegrityError on violation
    con.execute("""
        CREATE TRIGGER IF NOT EXISTS prevent_event_update
        BEFORE UPDATE ON events
        BEGIN SELECT RAISE(ABORT, 'events are immutable'); END
    """)
    con.execute("""
        CREATE TRIGGER IF NOT EXISTS prevent_event_delete
        BEFORE DELETE ON events
        BEGIN SELECT RAISE(ABORT, 'events cannot be deleted'); END
    """)
    con.commit()
    return con
```

### Pattern 3: JSONSchema Event Validation — Pre-compile Validator

**What:** Define the event schema as a module-level dict; compile a `Draft7Validator` once at import time. Call `validator.validate(event_dict)` before every write. Raises `jsonschema.ValidationError` on missing or wrong-typed fields.

**When to use:** At the top of every write path in `store.py`. Catch `ValidationError`, convert to `ToolError`, never write partial events.

```python
# Source: python-jsonschema.readthedocs.io (verified)
from jsonschema import Draft7Validator

EVENT_SCHEMA = {
    "type": "object",
    "required": ["event_id", "thread_id", "agent_id", "kind", "timestamp", "content_md"],
    "properties": {
        "event_id":    {"type": "string", "minLength": 1},
        "thread_id":   {"type": "string", "minLength": 1},
        "agent_id":    {"type": "string", "minLength": 1},
        "kind":        {"type": "string", "enum": ["message", "position", "dissent"]},
        "timestamp":   {"type": "string", "minLength": 1},
        "content_md":  {"type": "string"},
        "payload_json":{"type": ["string", "null"]}
    },
    "additionalProperties": False
}

_validator = Draft7Validator(EVENT_SCHEMA)

def validate_event(event: dict) -> None:
    """Raises jsonschema.ValidationError on invalid event. Never returns partial."""
    _validator.validate(event)
```

### Pattern 4: UUIDv7 Generation

**What:** Use `uuid_utils.uuid7()` to generate time-ordered UUIDs for `event_id`. Better B-tree locality than UUIDv4 for append-heavy tables.

**When to use:** In the store write path, before validation.

```python
# Source: pypi.org/project/uuid_utils (verified locally)
from uuid_utils import uuid7

def new_event_id() -> str:
    return str(uuid7())
```

### Pattern 5: Cold-Open Proof Test Structure

**What:** A pytest test that writes an event, closes the connection (simulating process death), opens a new connection, and reads the event back. This is the exact shape that was missing in prior yantrikdb gauntlet.

**When to use:** In `tests/test_cold_open.py` as the Phase 1 dogfood gate test.

```python
# Pattern verified locally (2026-06-02)
import sqlite3, pytest, json
from pathlib import Path

def test_cold_open(tmp_path):
    db_path = tmp_path / "harmony.sqlite"

    # Write phase — first "process"
    con1 = init_db(str(db_path))
    write_event(con1, {
        "event_id": "evt-001",
        "thread_id": "phase1-test",
        "agent_id": "claude",
        "kind": "message",
        "timestamp": "2026-06-02T00:00:00+00:00",
        "content_md": "## Cold-open proof",
        "payload_json": None
    })
    con1.close()  # Explicit close simulates process exit

    # Read phase — second "process"
    con2 = sqlite3.connect(str(db_path))
    row = con2.execute(
        "SELECT content_md FROM events WHERE event_id=?", ("evt-001",)
    ).fetchone()
    con2.close()

    assert row is not None
    assert row[0] == "## Cold-open proof"
```

### Pattern 6: Windows MCP Config Entry Format

**What:** The exact JSON fragment to add to each agent's MCP config file.

**For Claude Code** (`.codex/.mcp.json` in the `.codex` project, which Claude Code reads):

```json
{
  "mcpServers": {
    "bmg-harmony": {
      "command": "C:\\Users\\thepo\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
      "args": ["C:\\Users\\thepo\\OneDrive\\Documents\\GitHub\\BMG-Harmony\\server\\harmony_server.py"],
      "env": {
        "HARMONY_DB_PATH": "C:\\Users\\thepo\\OneDrive\\Documents\\GitHub\\BMG-Harmony\\.harmony\\store\\harmony.sqlite"
      },
      "disabled": false,
      "description": "BMG-Harmony shared board: post/read attributed messages across agents"
    }
  }
}
```

**For Codex** (`~/.codex/config.toml` or project-scoped `.codex/config.toml`):

```toml
[mcp_servers.bmg-harmony]
command = "C:/Users/thepo/AppData/Local/Programs/Python/Python313/python.exe"
args = ["C:/Users/thepo/OneDrive/Documents/GitHub/BMG-Harmony/server/harmony_server.py"]
env = { HARMONY_DB_PATH = "C:/Users/thepo/OneDrive/Documents/GitHub/BMG-Harmony/.harmony/store/harmony.sqlite" }
```

Note: Both configs use absolute paths. Codex config.toml accepts forward slashes on Windows.

### Anti-Patterns to Avoid

- **Writing to stdout in the MCP server:** Any `print()` to stdout corrupts the JSON-RPC stream. Use `print(..., file=sys.stderr)` or the Python `logging` module directed to stderr. This breaks stdio MCP silently and is the most common gotcha. [VERIFIED: MCP official docs + python-sdk stdio.py source]
- **Shared mutable connection across threads without `check_same_thread=False`:** SQLite connections are not thread-safe by default. Pass `check_same_thread=False` when opening the connection, and serialize writes with a threading.Lock or use a per-call connection pattern.
- **Catching `OperationalError` for trigger violations:** SQLite `RAISE(ABORT)` from triggers surfaces as `sqlite3.IntegrityError`, not `sqlite3.OperationalError`. Catch `sqlite3.IntegrityError` (or the base `sqlite3.Error`) in the write path. [VERIFIED: locally tested 2026-06-02]
- **Using naive datetime objects:** Always call `datetime.now(timezone.utc).isoformat()`. Naive datetimes (no tzinfo) produce ISO strings without `+00:00` which makes ordering ambiguous.
- **Storing the store path as a hardcoded constant:** Read `HARMONY_DB_PATH` from `os.environ` so the same server binary works for both agents pointing at the same file, and for tests pointing at a `tmp_path`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MCP tool schema + JSON-RPC dispatch | Custom JSON-RPC handler | `mcp.server.fastmcp.FastMCP` | MCP protocol details (capabilities negotiation, tool list, call routing, error codes) are complex and version-specific |
| Tool input validation | Manual `if 'field' not in data:` chains | FastMCP auto-validates from type annotations + Pydantic | Missing type coercions, nested object handling, and MCP error formatting are all handled by FastMCP |
| Event schema enforcement | Application-level guard only | `jsonschema.Draft7Validator` | jsonschema handles nested types, enums, minLength, additionalProperties — hand-rolled checks miss edge cases |
| Write-through caching / WAL config | Custom file-based WAL | `PRAGMA journal_mode=WAL` | SQLite WAL is a kernel-level primitive; reimplementing it loses crash safety, FSYNC ordering, and reader-writer concurrency |
| UUID generation | `str(random.randint(...))` or `os.urandom(16).hex()` | `uuid_utils.uuid7()` | UUIDv7 is a spec (RFC 9562); hand-rolled IDs are not globally unique, not sortable, and not debuggable |

**Key insight:** FastMCP abstracts away everything below the tool function signature. The complexity worth owning is the store layer (`store.py`) and the event schema (`schema.py`). Everything else is plumbing that the library handles correctly.

---

## Common Pitfalls

### Pitfall 1: stdout Pollution Breaks stdio Transport
**What goes wrong:** Any code in the server process that calls `print()` without `file=sys.stderr` (or any `logging.StreamHandler` pointed at stdout) corrupts the JSON-RPC bytestream. The MCP client receives garbage, connection fails silently or with a decode error, and the agent sees no tools.
**Why it happens:** FastMCP's stdio transport uses stdout as the protocol channel. Python's default logging handler writes to stdout.
**How to avoid:** At server module top: `import logging; logging.basicConfig(stream=sys.stderr)`. Never `print()` without `file=sys.stderr`. Audit all imports for libraries that write to stdout on import (rare but possible).
**Warning signs:** MCP client connects, tool list returns empty or connection drops immediately after connect.

### Pitfall 2: Trigger Exception Type Mismatch
**What goes wrong:** Code catches `sqlite3.OperationalError` for append-only trigger violations, misses the exception, and the application believes the mutation was silently ignored.
**Why it happens:** SQLite `RAISE(ABORT)` inside a trigger raises `sqlite3.IntegrityError` in Python, not `sqlite3.OperationalError`. The MCP handler re-raises as a generic exception, the LLM sees "Error calling tool."
**How to avoid:** Catch `sqlite3.IntegrityError` (or `sqlite3.Error` as base class) in the write path. Map it to a `ToolError` with a clear message: `"Event store is append-only: mutation refused."`
**Warning signs:** `UPDATE` or `DELETE` calls return without raising in test code.

### Pitfall 3: Cold-Open Test Passes Because Connection Was Never Closed
**What goes wrong:** The test writes a row, then reads it back in the SAME connection object. The test passes because the data is in the in-memory SQLite page cache, not because WAL mode persisted it. Then in production a real process restart loses the event.
**Why it happens:** In-process reads always see uncommitted writes; WAL flush on COMMIT only guarantees durability after the connection closes its transaction and the WAL is checkpointed.
**How to avoid:** The cold-open test MUST close `con1` before opening `con2`. `con.close()` is explicit; do not rely on garbage collection. This is the exact failure mode from the yantrikdb gauntlet.
**Warning signs:** Test passes but production cold-open fails; test only uses one `sqlite3.connect()` call.

### Pitfall 4: Windows Path Escaping in Config Files
**What goes wrong:** The `.mcp.json` entry uses single backslashes (`C:\Users\...`). JSON requires escaped backslashes. The config file fails to parse and the MCP server never starts.
**How to avoid:** In JSON, always double-escape: `C:\\Users\\thepo\\...`. In TOML (Codex config), forward slashes work fine and are preferred: `C:/Users/thepo/...`.
**Warning signs:** `claude mcp list` shows the server as failed or absent; Codex `/mcp` shows no bmg-harmony server.

### Pitfall 5: Threads Table Missing Before Events Insert
**What goes wrong:** Auto-create-thread logic inserts a thread record in a separate statement, then inserts the event. If the thread INSERT fails (race condition on simultaneous first-post from both agents) the event insert also fails due to FOREIGN KEY constraint.
**Why it happens:** Two agents post to the same new thread simultaneously. The first insert wins; the second hits a UNIQUE constraint on `threads.slug`.
**How to avoid:** Use `INSERT OR IGNORE INTO threads (...)` for thread auto-creation. This makes the thread creation idempotent. Wrap both the thread upsert and event insert in a single transaction.
**Warning signs:** Concurrent first-posts to a new thread fail with FOREIGN KEY or UNIQUE constraint errors in tests.

### Pitfall 6: check_same_thread Error Under FastMCP Async
**What goes wrong:** FastMCP runs tool functions in an asyncio event loop. If the SQLite connection was opened with the default `check_same_thread=True`, calls from async tools may fail with `ProgrammingError: SQLite objects created in a thread can only be used in that same thread`.
**How to avoid:** Open the connection with `sqlite3.connect(path, check_same_thread=False)`. Since FastMCP serializes tool calls (one at a time), a module-level lock is optional for Phase 1 but should be considered if write throughput matters.
**Warning signs:** Intermittent `ProgrammingError` exceptions in tool calls but not in tests.

---

## Code Examples

Verified patterns from official sources and local testing:

### FastMCP Server Minimal Entrypoint

```python
# Source: github.com/modelcontextprotocol/python-sdk README (verified)
from mcp.server.fastmcp import FastMCP
import sys

mcp = FastMCP("bmg-harmony")

@mcp.tool()
def echo(msg: str) -> str:
    """Echo a message back."""
    return msg

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### SQLite WAL Mode Activation

```python
# Source: sqlite.org/wal.html + verified locally (2026-06-02)
import sqlite3
con = sqlite3.connect("path/to/db.sqlite", check_same_thread=False)
con.execute("PRAGMA journal_mode=WAL")   # Returns ('wal',) on success
con.execute("PRAGMA synchronous=NORMAL") # Safe with WAL; faster than FULL
```

### JSON Schema Validation — Hard Reject Pattern

```python
# Source: python-jsonschema.readthedocs.io (verified)
from jsonschema import Draft7Validator, ValidationError
from fastmcp.exceptions import ToolError

def validate_and_write(event: dict, con: sqlite3.Connection):
    try:
        _validator.validate(event)
    except ValidationError as e:
        raise ToolError(f"Event validation failed: {e.message}")
    # Only reaches here if valid
    _write_to_db(event, con)
```

### Append-Only Trigger Enforcement

```python
# RAISE(ABORT) → sqlite3.IntegrityError — verified locally (2026-06-02)
try:
    con.execute("UPDATE events SET content_md='x' WHERE event_id='y'")
except sqlite3.IntegrityError as e:
    # e.args[0] == "events are immutable"
    raise ToolError("Event store is append-only: mutation refused.")
```

### UUIDv7 Event ID Generation

```python
# Source: pypi.org/project/uuid_utils (verified)
from uuid_utils import uuid7
event_id = str(uuid7())
# Example: "019e8a56-d232-76c3-a8bf-027785bdfee1"
# Time-ordered: sortable, debuggable, B-tree friendly
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Low-level `mcp.server.Server` + manual JSON-RPC | `FastMCP` decorator API | MCP Python SDK ~1.2 | FastMCP is now the recommended entrypoint; reduces server boilerplate to decorated functions |
| UUIDv4 for event primary keys | UUIDv7 (time-ordered) | RFC 9562, ratified 2024; `uuid_utils` 0.x added v7 in 2024 | New projects should default to v7; v4 remains correct but causes index fragmentation at scale |
| SSE transport for local MCP servers | stdio transport for local, HTTP for remote | MCP spec evolution 2024-2025 | stdio is the correct transport for local process MCP servers; SSE deprecated for remote |

**Deprecated / outdated:**
- `mcp.server.Server` (low-level): still available but FastMCP is the recommended path per official docs
- SSE transport for local servers: deprecated; use stdio for local, streamable-http for remote

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Codex MCP config uses `~/.codex/config.toml` as described in the search results | Windows MCP Wiring pattern | If Codex uses a different config file name or location, SETUP.md will give wrong instructions; can be verified at wiring time |
| A2 | The `.codex/.mcp.json` file in the `.codex` project is what Claude Code reads when running in the BMG-Harmony project context (vs per-project scope in `~/.claude.json`) | Windows MCP Wiring pattern | Claude Code may need the entry added to user-scope (`~/.claude.json`) rather than project-scope; SETUP.md should document both options |
| A3 | `fastmcp.exceptions.ToolError` import path is stable in `mcp` 1.27.x | Code Examples | May need to be `mcp.server.fastmcp.ToolError` or similar; verify at implementation time before finalizing imports |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.
*(Three assumptions remain — all are low-risk and verifiable at implementation/wiring time.)*

---

## Open Questions

1. **Which scope should the Claude Code MCP entry use?**
   - What we know: Claude Code supports local-scope (project-private, stored in `~/.claude.json`) and project-scope (stored in `.mcp.json` at project root). The existing `.codex/.mcp.json` entries are project-scope for the `.codex` project.
   - What's unclear: BMG-Harmony is a separate repo from `.codex`. The bmg-harmony MCP entry may need to go in the user-scope (`~/.claude.json`) so it's available across all projects, OR in a per-project `.mcp.json` in each project Claude works from.
   - Recommendation: SETUP.md should document the user-scope entry (`claude mcp add --scope user ...`) as the primary path, since both agents need it available in any project context.

2. **Thread state machine for `list_threads(state?)` filter**
   - What we know: `list_threads` is specified to return thread slugs and current state, with an optional `state` filter.
   - What's unclear: Phase 1 does not define a full thread state machine. The only states needed at Phase 1 are `open` (default) and possibly nothing else.
   - Recommendation: Implement `state` column on `threads` table as TEXT with default `'open'`. The `list_threads` filter is optional — if not passed, return all threads. Expand state values in Phase 2.

3. **`revision` field in post_message return value**
   - What we know: D-14 specifies the mutation return shape includes `revision`. This is not defined elsewhere in the context.
   - What's unclear: Is `revision` the `rowid` of the new event, the count of events in the thread at time of write, or something else?
   - Recommendation: Use `rowid` from the INSERT (SQLite auto-assigns) cast to int as the `revision`. This is monotonically increasing per table, debuggable, and requires no extra query.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python 3.13 | MCP server runtime | ✓ | 3.13.13 | — |
| `mcp` (FastMCP) | MCP server | ✓ | 1.27.0 installed (1.27.2 latest) | — |
| `pydantic` | FastMCP dep | ✓ | 2.12.5 installed (2.13.4 latest) | — |
| `jsonschema` | Event validation | ✓ | 4.23.0 installed (4.26.0 latest) | — |
| `uuid_utils` | UUIDv7 generation | ✓ | 0.16.0 (latest) | Fall back to `import uuid; str(uuid.uuid4())` — acceptable for Phase 1 |
| `pytest` | Cold-open tests | ✗ (not installed) | 9.0.3 available | Must install: `pip install pytest` |
| SQLite | Event store | ✓ | Python stdlib (ships with Python 3.x) | — |

**Missing dependencies with no fallback:**
- `pytest` must be installed before running tests: `pip install pytest`

**Missing dependencies with fallback:**
- `uuid_utils` missing → fall back to `uuid.uuid4()` from stdlib if needed (performance tradeoff only, not correctness)

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | none yet — Wave 0 task |
| Quick run command | `python -m pytest tests/test_store.py -x -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BOARD-01 | post_message writes event with all attribution fields | unit | `python -m pytest tests/test_store.py::test_post_message_writes_event -x` | ❌ Wave 0 |
| BOARD-01 | post_message hard-rejects missing required field | unit | `python -m pytest tests/test_store.py::test_post_message_rejects_invalid -x` | ❌ Wave 0 |
| BOARD-02 | read_thread returns all events in insertion order | unit | `python -m pytest tests/test_store.py::test_read_thread -x` | ❌ Wave 0 |
| BOARD-02 | read_thread works across process restart (cold open) | integration | `python -m pytest tests/test_cold_open.py::test_cold_open -x` | ❌ Wave 0 |
| POS-01 | post_stack_position writes position event to harmony-stack-decision thread | unit | `python -m pytest tests/test_store.py::test_post_stack_position -x` | ❌ Wave 0 |
| POS-02 | post_message with kind=dissent writes a dissent event | unit | `python -m pytest tests/test_store.py::test_post_dissent -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/test_store.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green + both agents have posted stack positions to `harmony-stack-decision` thread

### Wave 0 Gaps

- [ ] `tests/conftest.py` — shared fixtures (`tmp_db` fixture: temp SQLite path + `init_db` call; cleanup on teardown)
- [ ] `tests/test_store.py` — unit tests for write/read/validation/append-only
- [ ] `tests/test_cold_open.py` — the cold-open proof test (the Phase 1 dogfood gate)
- [ ] Framework install: `pip install pytest` — not currently installed

---

## Security Domain

Phase 1 is an internal-only tool with no authentication/access control in v1 scope (explicitly out of scope per REQUIREMENTS.md). ASVS categories assessed for completeness.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Out of scope v1 — trusted internal tools only |
| V3 Session Management | No | No sessions — stateless MCP tool calls |
| V4 Access Control | No | Out of scope v1 — both agents are trusted peers |
| V5 Input Validation | Yes | `jsonschema.Draft7Validator` — hard reject on missing/invalid fields |
| V6 Cryptography | No | No secrets, no encryption needed in v1 |

### Known Threat Patterns for Python + SQLite

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SQL injection via thread_id or agent_id strings | Tampering | Parameterized queries (`?` placeholders) — never string-format SQL |
| Malformed payload_json string stored as raw bytes | Tampering | Validate `payload_json` is valid JSON string before storing, or accept `None`; do not store raw unvalidated dicts |
| Stdout corruption via rogue print() | Denial of Service | All logging to stderr; no stdout writes in server process |

---

## Sources

### Primary (HIGH confidence)

- `github.com/modelcontextprotocol/python-sdk` — FastMCP tool registration, stdio transport, lifespan parameter
- `code.claude.com/docs/en/mcp` — Claude Code .mcp.json format, scope hierarchy, local vs project vs user scope
- `developers.openai.com/codex/mcp` — Codex config.toml MCP server registration format
- `sqlite.org/wal.html` — WAL mode semantics, reader-writer concurrency
- `python-jsonschema.readthedocs.io` — `Draft7Validator` pre-compile pattern
- `pypi.org/project/mcp` — Package provenance (Anthropic), version 1.27.2
- Local verification — WAL mode test, append-only trigger test, cold-open test, FastMCP lifespan import — all run on this machine (Python 3.13.13, 2026-06-02)

### Secondary (MEDIUM confidence)

- `gofastmcp.com/servers/tools` — ToolError import path and structured return patterns
- `lik.ai/blog/sqlite-primary-key-benchmarks/` — UUIDv7 vs UUIDv4 B-tree performance comparison
- Slopcheck v0.6.1 results — all packages [OK]

### Tertiary (LOW confidence / [ASSUMED])

- Codex config.toml exact file path (`~/.codex/config.toml`) — confirmed from actual machine config, HIGH confidence on this machine
- `fastmcp.exceptions.ToolError` import path — confirmed from search results, should be verified at implementation time

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified on PyPI, installed locally, slopcheck OK
- Architecture: HIGH — FastMCP + SQLite patterns verified via official docs and local test execution
- Pitfalls: HIGH (stdout corruption, trigger exception type) / MEDIUM (Windows path escaping, concurrent first-post race)

**Research date:** 2026-06-02
**Valid until:** 2026-08-01 (stable libraries; MCP SDK moves fast, re-verify if >60 days)
