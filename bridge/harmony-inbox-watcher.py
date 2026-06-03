#!/usr/bin/env python3
"""
harmony-inbox-watcher.py — Zero-token board watcher for harmony-inbox-claude.

Polls the harmony SQLite store directly (no MCP, no model) for unacked messages
from trusted agents in the 'harmony-inbox-claude' thread. When found, fires the
headless claude-worker with full-auto (AllowBash) to execute the task.

SAFETY MODEL (watertight by design):
  - Read-only SQLite poll: watcher never writes to the DB directly
  - Dispatch-before-fire: message is logged BEFORE Claude launches; no retry if watcher crashes
  - Watcher acks via Claude: Claude's first action is ack_message — immutable board receipt
  - Dedup via local dispatch ledger: never re-fires a message already dispatched
  - Cooldown between invocations
  - Daily cap on invocations
  - Consecutive failure circuit breaker (halts + creates kill switch on threshold)
  - Kill-switch file: touch STOP-HARMONY-WATCHER to halt immediately
  - Trusted-agent filter: only fires on messages from TRUSTED_AGENTS
  - Message size guard: rejects payloads > MAX_PROMPT_CHARS

Usage:
  python harmony-inbox-watcher.py [--db PATH] [--poll SECS] [--cooldown SECS]
                                  [--max-daily N] [--max-fail N] [--once]
"""

import argparse
import json
import logging
import os
import sqlite3
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

# ── config defaults ──────────────────────────────────────────────────────────
HARMONY_DB     = r"C:\Users\thepo\OneDrive\Documents\GitHub\BMG-Harmony\.harmony\store\harmony.sqlite"
INBOX_THREAD   = "harmony-inbox-claude"
TRUSTED_AGENTS = {"codex"}
WORKER_SCRIPT  = r"C:\Users\thepo\OneDrive\Documents\GitHub\BMG-Harmony\bridge\claude-worker.ps1"
DEFAULT_WORKDIR = r"C:\Users\thepo\OneDrive\Documents\GitHub\BMG-Brain"
WATCHER_AGENT  = "harmony-watcher"

POLL_INTERVAL    = 30     # seconds between idle polls
COOLDOWN         = 60     # min seconds between consecutive worker fires
MAX_DAILY        = 20     # hard cap: max fires per calendar day
MAX_CONSEC_FAIL  = 3      # halt + create kill switch after N consecutive failures
MAX_PROMPT_CHARS = 8_000  # reject payloads larger than this
WORKER_TIMEOUT   = 600    # seconds before killing a hung worker (10 min)

_TEMP = Path(os.environ.get("TEMP", "/tmp"))
KILL_SWITCH    = _TEMP / "STOP-HARMONY-WATCHER"
DISPATCH_FILE  = _TEMP / "harmony-watcher-dispatched.json"
LOG_DIR        = _TEMP
# ─────────────────────────────────────────────────────────────────────────────


def setup_logging() -> Path:
    log_path = LOG_DIR / f"harmony-watcher-{date.today().isoformat()}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return log_path


def load_ledger() -> dict:
    if DISPATCH_FILE.exists():
        try:
            return json.loads(DISPATCH_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_ledger(ledger: dict) -> None:
    DISPATCH_FILE.write_text(json.dumps(ledger, indent=2), encoding="utf-8")


def poll_inbox(db_path: str):
    """
    Return the oldest message in INBOX_THREAD not yet acked by WATCHER_AGENT,
    or None if the inbox is empty. Opens the DB read-only — watcher never mutates.
    """
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Harmony DB not found: {db_path}. Is the server initialized?")

    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        row = con.execute(
            """
            SELECT e.event_id, e.agent_id, e.content_md, e.timestamp
            FROM   events e
            WHERE  e.thread_id = ?
              AND  e.kind IN ('message', 'position')
              AND  NOT EXISTS (
                       SELECT 1 FROM message_acks ma
                       WHERE ma.message_id = e.event_id
                         AND ma.agent_id   = ?
                   )
            ORDER BY e.rowid
            LIMIT 1
            """,
            (INBOX_THREAD, WATCHER_AGENT),
        ).fetchone()
    finally:
        con.close()
    return row  # (event_id, agent_id, content_md, timestamp) or None


def parse_workdir(content_md: str) -> str:
    """Extract optional 'WORKDIR: <path>' directive from message; else DEFAULT_WORKDIR."""
    for line in content_md.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("WORKDIR:"):
            return stripped[8:].strip()
    return DEFAULT_WORKDIR


def build_prompt(event_id: str, agent_id: str, content_md: str) -> str:
    workdir = parse_workdir(content_md)
    return (
        f"HARMONY TASK — dispatched by harmony-inbox-watcher.\n"
        f"Message ID : {event_id}\n"
        f"From       : {agent_id}\n"
        f"Thread     : {INBOX_THREAD}\n"
        f"WorkDir    : {workdir}\n\n"
        f"STEP 1 (required first): Call bmg-harmony ack_message with "
        f"message_id={event_id} and agent_id={WATCHER_AGENT}. This is the immutable "
        f"delivery receipt. Do it before any other action.\n\n"
        f"STEP 2: Execute the task below as a full UAE pass in '{workdir}'. "
        f"Lead with brain: recall yantrikdb memory, re-read coarse live surfaces "
        f"(.planning/STATE.md, last after-packet, relevant harmony threads), synthesize "
        f"the invariant ledger (BMG-Brain coordinates; repo owns implementation truth; "
        f"memory/tools are context; UAE governs evidence, receipt, commit, push, closeout). "
        f"One proving intent per pass. Failure-loop hard stop after 2 strikes. "
        f"UAE closeout: git status → commit → git pull --ff-only → git push → "
        f"git status -sb → after-packet receipt. If push is blocked, record INCOMPLETE "
        f"with explicit reason — never a silent third state.\n\n"
        f"STEP 3: Write durable learnings (decisions, corrections, friction patterns) to "
        f"the flywheel via yantrikdb memory. Green summaries alone are weak evidence.\n\n"
        f"STEP 4: Post a one-line completion status to harmony thread 'harmony-watcher-log' "
        f"(agent_id=claude, kind=message) with: task summary | outcome (DONE / INCOMPLETE) "
        f"| commit hash if any.\n\n"
        f"=== TASK FROM CODEX ===\n{content_md}\n=== END TASK ==="
    )


def fire_worker(event_id: str, agent_id: str, content_md: str) -> int:
    workdir    = parse_workdir(content_md)
    prompt     = build_prompt(event_id, agent_id, content_md)

    # Write prompt to a temp file — avoids list2cmdline quoting corruption when
    # the prompt contains newlines, backslashes, or other special characters.
    prompt_file = _TEMP / f"harmony-worker-prompt-{event_id[:8]}.txt"
    prompt_file.write_text(prompt, encoding="utf-8")

    cmd = [
        "powershell", "-ExecutionPolicy", "Bypass",
        "-File",       WORKER_SCRIPT,
        "-PromptFile", str(prompt_file),
        "-WorkDir",    workdir,
        "-AllowBash",
    ]
    logging.info(f"  Firing worker | event={event_id} | workdir={workdir}")
    try:
        result = subprocess.run(cmd, timeout=WORKER_TIMEOUT)
    finally:
        prompt_file.unlink(missing_ok=True)  # clean up temp file
    return result.returncode


def daily_count(ledger: dict, today: str) -> int:
    return sum(1 for v in ledger.values() if v.get("date") == today and v.get("outcome") != "IGNORED_UNTRUSTED" and v.get("outcome") != "IGNORED_TOO_LARGE")


def main() -> None:
    parser = argparse.ArgumentParser(description="Harmony inbox watcher for Claude")
    parser.add_argument("--db",        default=HARMONY_DB,    help="Path to harmony.sqlite")
    parser.add_argument("--poll",      type=int, default=POLL_INTERVAL, help="Poll interval (s)")
    parser.add_argument("--cooldown",  type=int, default=COOLDOWN,      help="Min seconds between fires")
    parser.add_argument("--max-daily", type=int, default=MAX_DAILY,     help="Max fires per day")
    parser.add_argument("--max-fail",  type=int, default=MAX_CONSEC_FAIL, help="Consecutive failure halt threshold")
    parser.add_argument("--once",      action="store_true",  help="Fire once if a task is waiting, then exit")
    args = parser.parse_args()

    log_path = setup_logging()
    logging.info("=== harmony-inbox-watcher starting ===")
    logging.info(f"DB          : {args.db}")
    logging.info(f"Inbox       : {INBOX_THREAD}  (trusted agents: {sorted(TRUSTED_AGENTS)})")
    logging.info(f"Poll        : {args.poll}s  |  Cooldown: {args.cooldown}s")
    logging.info(f"Guards      : daily_cap={args.max_daily}  consec_fail_halt={args.max_fail}")
    logging.info(f"Kill switch : {KILL_SWITCH}  (touch this file to stop)")
    logging.info(f"Dispatch log: {DISPATCH_FILE}")
    logging.info(f"Log         : {log_path}")

    # Clear any leftover kill switch from a previous halt (require deliberate restart)
    if KILL_SWITCH.exists():
        logging.warning(f"Kill switch present from previous session — removing to start fresh.")
        KILL_SWITCH.unlink()

    ledger       = load_ledger()
    consec_fail  = 0
    last_fire_ts = 0.0

    while True:
        today = date.today().isoformat()

        # ── kill switch ─────────────────────────────────────────────────────
        if KILL_SWITCH.exists():
            logging.warning("Kill switch present — halting watcher cleanly.")
            break

        # ── consecutive failure circuit breaker ─────────────────────────────
        if consec_fail >= args.max_fail:
            logging.error(
                f"Consecutive failure limit ({args.max_fail}) reached. "
                f"Halting to prevent runaway. Delete {KILL_SWITCH} and restart to resume."
            )
            KILL_SWITCH.touch()  # require deliberate restart
            break

        # ── daily cap ────────────────────────────────────────────────────────
        dc = daily_count(ledger, today)
        if dc >= args.max_daily:
            logging.warning(f"Daily cap reached ({dc}/{args.max_daily}). Sleeping {args.poll}s.")
            time.sleep(args.poll)
            continue

        # ── poll ─────────────────────────────────────────────────────────────
        try:
            row = poll_inbox(args.db)
        except FileNotFoundError as exc:
            logging.error(str(exc))
            time.sleep(args.poll)
            continue
        except Exception as exc:
            logging.error(f"Poll error: {exc}")
            consec_fail += 1
            time.sleep(args.poll)
            continue

        if row is None:
            if args.once:
                logging.info("--once: no pending task found, exiting.")
                break
            time.sleep(args.poll)
            continue

        event_id, agent_id, content_md, timestamp = row

        # ── dedup: already dispatched? ────────────────────────────────────
        if event_id in ledger:
            logging.debug(f"Already dispatched: {event_id}")
            if args.once:
                break
            time.sleep(args.poll)
            continue

        # ── trusted agent? ────────────────────────────────────────────────
        if agent_id not in TRUSTED_AGENTS:
            logging.warning(f"Ignoring message from untrusted agent '{agent_id}': {event_id}")
            ledger[event_id] = {"date": today, "agent": agent_id, "outcome": "IGNORED_UNTRUSTED"}
            save_ledger(ledger)
            if args.once:
                break
            time.sleep(args.poll)
            continue

        # ── size guard ────────────────────────────────────────────────────
        if len(content_md) > MAX_PROMPT_CHARS:
            logging.warning(
                f"Message {event_id} too large ({len(content_md):,} chars > {MAX_PROMPT_CHARS:,}) — skipping."
            )
            ledger[event_id] = {"date": today, "agent": agent_id, "outcome": "IGNORED_TOO_LARGE"}
            save_ledger(ledger)
            if args.once:
                break
            time.sleep(args.poll)
            continue

        # ── cooldown ──────────────────────────────────────────────────────
        elapsed = time.time() - last_fire_ts
        if elapsed < args.cooldown:
            wait = args.cooldown - elapsed
            logging.info(f"Cooldown: {wait:.0f}s remaining before next fire.")
            time.sleep(min(wait, args.poll))
            continue

        # ── dispatch (record BEFORE fire — prevents double-dispatch on crash) ──
        logging.info(f">>> Task received | event={event_id} | from={agent_id} | {timestamp}")
        ledger[event_id] = {
            "date":          today,
            "agent":         agent_id,
            "dispatched_at": datetime.utcnow().isoformat(),
            "outcome":       "PENDING",
        }
        save_ledger(ledger)
        last_fire_ts = time.time()

        # ── fire ─────────────────────────────────────────────────────────
        try:
            rc = fire_worker(event_id, agent_id, content_md)
            outcome = "DONE" if rc == 0 else f"FAILED(rc={rc})"
            consec_fail = 0 if rc == 0 else consec_fail + 1
        except subprocess.TimeoutExpired:
            logging.error(f"Worker timed out ({WORKER_TIMEOUT}s) for event {event_id}")
            outcome    = "TIMEOUT"
            consec_fail += 1
        except Exception as exc:
            logging.error(f"Worker exception for event {event_id}: {exc}")
            outcome    = f"EXCEPTION:{exc}"
            consec_fail += 1

        ledger[event_id]["outcome"] = outcome
        save_ledger(ledger)
        logging.info(f"<<< Task finished | event={event_id} | outcome={outcome} | consec_fail={consec_fail}")

        if args.once:
            break

        time.sleep(args.poll)

    logging.info("=== harmony-inbox-watcher stopped ===")


if __name__ == "__main__":
    main()
