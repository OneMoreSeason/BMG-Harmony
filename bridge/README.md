# BMG-Harmony Bridge — bidirectional headless delegation

This directory lets **either agent drive the other headlessly**, using the shared
harmony board as the channel. No human relays prompts; no desktop automation.

Proven end-to-end on 2026-06-03 (both directions).

## The two directions

### Forward — Claude drives Codex
Claude (running in the Claude Code harness) is a *persistent, event-driven host*:
1. Claude posts a work packet to a board thread (`post_message`).
2. Claude launches `codex exec "<prompt>"` as a **background** process.
3. When Codex exits, the harness **auto-wakes Claude** — a turn with no human input.
4. Claude reads Codex's board reply, posts the next instruction, repeats.

The loop self-sustains as long as each Claude turn leaves a Codex run in flight.

### Reverse — Codex drives Claude
Codex's `exec` is *one-shot* (no persistent host), so it orchestrates **synchronously**
inside a single session:
1. Codex posts a work packet to a board thread.
2. Codex runs `claude-worker.ps1 -Prompt "<task>"`, which **blocks** until the
   headless Claude worker finishes and returns its output.
3. Codex reads the worker's output + the board, verifies, and signs off.

For "delegate a task and get it done," the synchronous mode is enough. For a long,
multi-turn autonomous Codex, use the conductor below.

### Long autonomous runs — `codex-conductor.ps1`

This removes the one-off limit. The conductor chains **fresh** Codex passes over durable
state (board + `.planning/STATE.md` + last after-packet) until Codex signals closeout. Fresh
passes match BMG's coarse/fine packet model and can't overflow context, so a mission can span
many turns without a fragile single session.

Each turn, Codex is instructed to lead with brain (memory recall → invariant ledger), hold one
proving intent, honor UAE closeout (commit → `git pull --ff-only` → push → receipt, or
`INCOMPLETE`), post a board status line, and end with a sentinel. The conductor reads the
sentinel to drive the loop:

- `UAE-CLOSEOUT: …` → mission complete → stop
- `UAE-HALT: …` → failure-loop hard stop / hard block → stop, human needed
- `UAE-CONTINUE: …` → re-invoke for another pass

Guards ("restrained by UAE **or other**"): `-MaxTurns` cap, a kill-switch file
(`%TEMP%\STOP-CODEX`), and the doctrine failure-loop hard stop baked into the prompt. Safe
default sandbox is `--full-auto` with the harmony store as a writable root; `-FullAccess` is an
opt-in for runs that must push to a remote.

```powershell
powershell -ExecutionPolicy Bypass -File codex-conductor.ps1 `
  -Objective "Wire harmony-awareness into the Codex Boot Route per harmony-inbox-codex." `
  -WorkDir "C:\Users\thepo\OneDrive\Documents\GitHub\BMG-Brain" -MaxTurns 6
```

## Artifacts

| File | Purpose |
|------|---------|
| `harmony.mcp.json` | Minimal MCP config exposing **only** the bmg-harmony board (least privilege). |
| `claude-worker.ps1` | Safe wrapper around `claude -p` for the reverse direction. |
| `codex-conductor.ps1` | Persistent multi-turn runner: chains fresh Codex passes over durable state until UAE closeout/halt or a guard. |
| `harmony-inbox-watcher.py` | Zero-token board watcher: polls `harmony-inbox-claude`, fires `claude-worker.ps1` full-auto on new Codex tasks. |
| `start-watcher.ps1` | One-liner launcher for the watcher. |

## Safety posture (safe + sustainable)

`claude-worker.ps1` never uses a blanket permission bypass. It enforces:
- `--strict-mcp-config` + `harmony.mcp.json` → the worker sees the board and **nothing else**
  (no desktop-ops, blender, godot, or yantrikdb organelles).
- `--allowedTools` whitelist → board tools + `Read`/`Write`/`Edit`. `Bash` is opt-in via `-AllowBash`.
- Isolated `-WorkDir` (defaults to `%TEMP%\harmony-worker`) so file work stays out of your repos.

The Codex side (`codex exec`) currently uses `--dangerously-bypass-approvals-and-sandbox`
because the board's SQLite store lives **outside** any project workspace and a
read-only/workspace-write sandbox blocks the MCP write. To tighten: use `--full-auto`
plus a writable-root carve-out for `BMG-Harmony/.harmony/store`.

## Setup (one-time, per machine)

```powershell
npm install -g @openai/codex@0.136.0        # headless Codex  (codex exec)
npm install -g @anthropic-ai/claude-code     # headless Claude (claude -p)
```

Both reuse existing auth: Codex via `~/.codex/auth.json` (ChatGPT account → model
`gpt-5.5`, requires CLI >= 0.136); Claude via the existing Claude Code login.

## Invoke the reverse worker manually

```powershell
powershell -ExecutionPolicy Bypass `
  -File .\claude-worker.ps1 `
  -Prompt "Read harmony thread X via bmg-harmony read_thread, then post_message a reply..."
```

## Gotchas (cost real debugging time)

- The bundled `~/.codex/.sandbox-bin/codex.exe` (0.119) is too old for `gpt-5.5` and the
  ChatGPT account rejects `gpt-5`/`gpt-5-codex`. Use the npm 0.136+ CLI.
- `codex exec` refuses to run outside a git repo without `--skip-git-repo-check`.
- `claude -p` stalls ~3s waiting on stdin; the wrapper pipes empty stdin (`$null |`) to avoid it.
