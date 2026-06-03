# BMG-Harmony Setup Guide

This guide wires both Claude Code and Codex into the BMG-Harmony MCP server.
Copy-paste the config fragments for your agent and follow the verification steps.

---

## Section 1: Prerequisites

All dependencies are already installed on this machine.

| Dependency | Path / Command | Status |
|------------|---------------|--------|
| Python 3.13 | `C:/Users/thepo/AppData/Local/Programs/Python/Python313/python.exe` | Installed |
| `mcp` (FastMCP) | `pip show mcp` | Installed (1.27.0+) |
| `pydantic` | `pip show pydantic` | Installed (transitive) |
| `jsonschema` | `pip show jsonschema` | Installed |
| `uuid_utils` | `pip show uuid_utils` | Installed |
| `pytest` | `pip show pytest` | Installed |

The live SQLite store at `.harmony/store/harmony.sqlite` is **git-ignored** — it is created automatically on first server start and never committed.

---

## Section 2: Quick Start — Verify Server Starts

Run this in PowerShell to confirm the server starts cleanly before wiring into an agent:

```powershell
$env:HARMONY_DB_PATH = "C:/Users/thepo/OneDrive/Documents/GitHub/BMG-Harmony/.harmony/store/harmony.sqlite"
"C:/Users/thepo/AppData/Local/Programs/Python/Python313/python.exe" "C:/Users/thepo/OneDrive/Documents/GitHub/BMG-Harmony/server/harmony_server.py"
```

**Expected:** The process starts and waits for MCP input on stdin. No output on stdout (stderr log lines are fine). Press Ctrl+C to stop.

If you see `HARMONY_DB_PATH environment variable is not set` in stderr: the env var is not being passed. Check the `$env:HARMONY_DB_PATH` assignment above.

---

## Section 3: Claude Code Wiring

Claude Code reads MCP server config from `.mcp.json` files. The `.codex` project-level config at `C:/Users/thepo/OneDrive/Documents/GitHub/.codex/.mcp.json` is the target.

### Option A — JSON Edit (Recommended — sets env var correctly)

Open `C:/Users/thepo/OneDrive/Documents/GitHub/.codex/.mcp.json` and add the `"bmg-harmony"` entry under `"mcpServers"`. **Do not replace existing entries — merge.**

```json
"bmg-harmony": {
  "command": "C:\\Users\\thepo\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
  "args": ["C:\\Users\\thepo\\OneDrive\\Documents\\GitHub\\BMG-Harmony\\server\\harmony_server.py"],
  "env": {
    "HARMONY_DB_PATH": "C:\\Users\\thepo\\OneDrive\\Documents\\GitHub\\BMG-Harmony\\.harmony\\store\\harmony.sqlite"
  },
  "disabled": false,
  "description": "BMG-Harmony shared board: post/read attributed messages across agents"
}
```

**Critical:** All backslashes in JSON paths must be doubled (`\\`). Forward slashes do NOT work reliably in JSON MCP config on Windows.

After saving, verify with:
```
claude mcp list
```
Expected: `bmg-harmony` appears in the list. If it shows `failed`, check:
1. Python path is exactly `C:\\Users\\thepo\\AppData\\Local\\Programs\\Python\\Python313\\python.exe`
2. Server path is exactly `C:\\Users\\thepo\\OneDrive\\Documents\\GitHub\\BMG-Harmony\\server\\harmony_server.py`
3. The file is valid JSON (no trailing commas, all backslashes doubled)

### Option B — CLI Method (User-scope, available across all projects)

If you want bmg-harmony available in all Claude Code projects (not just `.codex`), use user-scope:

```
claude mcp add --scope user bmg-harmony "C:/Users/thepo/AppData/Local/Programs/Python/Python313/python.exe" -- "C:/Users/thepo/OneDrive/Documents/GitHub/BMG-Harmony/server/harmony_server.py"
```

Note: The CLI method may not support env vars directly. If `HARMONY_DB_PATH` is not passed, the server will fail to start with a clear error. Use Option A (JSON edit) for the `env` block.

---

## Section 4: Codex Wiring

Codex reads MCP server config from `config.toml`. The actual user-level config path on this machine is:
`C:/Users/thepo/.codex/config.toml`

> **Note:** SETUP.md originally documented `C:/Users/thepo/AppData/Roaming/.codex/config.toml` — that path does not exist on this machine. Codex confirmed the real path is `~/.codex/config.toml` during dogfood wiring (2026-06-03).

Add this section to `config.toml` (forward slashes work in TOML on Windows):

```toml
[mcp_servers.bmg-harmony]
command = "C:/Users/thepo/AppData/Local/Programs/Python/Python313/python.exe"
args = ["C:/Users/thepo/OneDrive/Documents/GitHub/BMG-Harmony/server/harmony_server.py"]
env = { HARMONY_DB_PATH = "C:/Users/thepo/OneDrive/Documents/GitHub/BMG-Harmony/.harmony/store/harmony.sqlite", PYTHONPATH = "C:/Users/thepo/OneDrive/Documents/GitHub/BMG-Harmony" }
```

> **Note:** `PYTHONPATH` is required when launching `server/harmony_server.py` by absolute path — without it Python can't resolve the `server` package import. Confirmed during dogfood wiring (2026-06-03).

After saving, verify in Codex:
```
/mcp
```
Expected: `bmg-harmony` listed as available. If absent, check that the TOML section header is `[mcp_servers.bmg-harmony]` (not nested incorrectly).

---

## Section 5: Dogfood Gate

After both agents are wired, each must call `post_stack_position` to confirm the shared store works end-to-end. This is a Phase 1 success criterion — not optional.

**Claude calls (in its MCP session):**
```python
post_stack_position(
    agent_id="claude",
    position_md="## Claude Stack Position\n\nAgreed stack: Python + SQLite WAL + append-only events + FastMCP. No embeddings in v1 core. YantrikDB = downstream flywheel export only. Phase 1 store and MCP server built and green."
)
```

**Codex calls (in its MCP session):**
```python
post_stack_position(
    agent_id="codex",
    position_md="## Codex Stack Position\n\nAgreed stack: Python + SQLite WAL + append-only events + FastMCP. Implementation authority confirmed. No embeddings. YantrikDB = downstream only. Phase 1 store verified."
)
```

**Verify both posts exist:**
```powershell
$env:HARMONY_DB_PATH = "C:/Users/thepo/OneDrive/Documents/GitHub/BMG-Harmony/.harmony/store/harmony.sqlite"
"C:/Users/thepo/AppData/Local/Programs/Python/Python313/python.exe" -c "
import os
os.environ['HARMONY_DB_PATH'] = 'C:/Users/thepo/OneDrive/Documents/GitHub/BMG-Harmony/.harmony/store/harmony.sqlite'
import sys; sys.path.insert(0, 'C:/Users/thepo/OneDrive/Documents/GitHub/BMG-Harmony')
from server.store import init_db, read_thread
con = init_db(os.environ['HARMONY_DB_PATH'])
events = read_thread(con, 'harmony-stack-decision')
con.close()
agent_ids = [e['agent_id'] for e in events]
print(f'Events in harmony-stack-decision: {len(events)}')
print(f'Agent IDs: {agent_ids}')
assert 'claude' in agent_ids, 'claude position missing'
assert 'codex' in agent_ids, 'codex position missing'
print('DOGFOOD GATE: PASSED')
"
```

Expected output:
```
Events in harmony-stack-decision: 2
Agent IDs: ['claude', 'codex']
DOGFOOD GATE: PASSED
```

---

## Section 6: Cold-Open Proof Test

Run the pytest suite to confirm store durability (WAL mode, cold-open pattern):

```powershell
cd "C:/Users/thepo/OneDrive/Documents/GitHub/BMG-Harmony"
"C:/Users/thepo/AppData/Local/Programs/Python/Python313/python.exe" -m pytest tests/ -v
```

Expected: All 8 tests pass (test_store.py x7, test_cold_open.py x1).

For just the cold-open proof:
```powershell
"C:/Users/thepo/AppData/Local/Programs/Python/Python313/python.exe" -m pytest tests/test_cold_open.py -v
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `HARMONY_DB_PATH environment variable is not set` | Env var missing from MCP config | Add `env` block to `.mcp.json` with double-backslash paths |
| `bmg-harmony` not in `claude mcp list` | Config file not saved / JSON invalid | Validate JSON: `python -c "import json, pathlib; json.loads(pathlib.Path('C:/Users/thepo/OneDrive/Documents/GitHub/.codex/.mcp.json').read_text()); print('OK')"` |
| `bmg-harmony` shows `failed` in `claude mcp list` | Python or server path wrong | Check both paths exist: `Test-Path "C:\Users\thepo\AppData\Local\Programs\Python\Python313\python.exe"` |
| `bmg-harmony` not in Codex `/mcp` | TOML syntax error or wrong file path | Open `C:/Users/thepo/AppData/Roaming/.codex/config.toml` and verify the `[mcp_servers.bmg-harmony]` section is well-formed |
| Store file not created | `.harmony/store/` directory missing | Create: `New-Item -ItemType Directory -Path "C:\Users\thepo\OneDrive\Documents\GitHub\BMG-Harmony\.harmony\store" -Force` |
