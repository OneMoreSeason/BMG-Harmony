"""Opt-in watcher for formal Claude task envelopes, never legacy inbox chatter."""
import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

from delegate import (DEFAULT_DB, DEFAULT_RUNS, ROOT, now, run_task, save_json,
                      validate_task)
from server.store import ack_message, init_db

INBOX_THREAD = "harmony-delegations-claude"
WATCHER_AGENT = "harmony-watcher"


def poll_inbox(db_path, ledger):
    """Scan in board order; an ignored/dispatched head cannot starve later tasks."""
    con = sqlite3.connect(f"file:{Path(db_path).resolve().as_posix()}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT event_id, agent_id, payload_json FROM events "
            "WHERE thread_id=? AND kind='message' ORDER BY rowid", (INBOX_THREAD,))
        for event_id, agent, raw in rows:
            if event_id in ledger or agent != "codex":
                continue
            try:
                data = json.loads(raw or "")
            except (ValueError, TypeError):
                continue
            if isinstance(data, dict) and data.get("type") == "harmony.delegation.task.v1":
                return event_id, data.get("task")
    finally:
        con.close()
    return None


def allowed_task(raw, allowed_roots, allow_implement=False):
    task = validate_task(raw)
    root = Path(task["workdir"]).resolve()
    # Exact repository/worktree roots, rather than a broad parent directory.
    if root not in {Path(p).resolve() for p in allowed_roots}:
        raise ValueError("Task workdir is not an explicitly allowed root")
    if task["mode"] == "implement" and not allow_implement:
        raise ValueError("Watcher implementation tasks were not enabled")
    return task


def load_ledger(path):
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Invalid dispatch ledger; refuse replay")
    return value


def dispatch_one(db, runs, ledger_path, allowed_roots, allow_implement=False, kill_switch=None):
    ledger = load_ledger(ledger_path)
    item = poll_inbox(db, ledger)
    if item is None:
        return None
    event_id, raw = item
    # Persist before validation/launch: failure or crash never auto-replays work.
    ledger[event_id] = {"status": "claimed", "claimed_at": now()}
    save_json(ledger_path, ledger)
    try:
        task = allowed_task(raw, allowed_roots, allow_implement)
        con = init_db(str(db))
        try:
            ack_message(con, event_id, WATCHER_AGENT)
        finally:
            con.close()
        state = run_task(task, runs, db, cancel_file=kill_switch)
        result = {"status": state["status"], "task_id": task["task_id"]}
    except Exception as exc:
        result = {"status": "rejected", "error": f"{type(exc).__name__}: {exc}"}
    ledger[event_id].update(result, finished_at=now())
    save_json(ledger_path, ledger)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enable", action="store_true", help="Explicitly run the watcher")
    parser.add_argument("--allowed-root", action="append", default=[])
    parser.add_argument("--allow-implement", action="store_true")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--state-dir", type=Path, default=ROOT / ".harmony/watcher")
    parser.add_argument("--kill-switch", type=Path,
                        default=Path(os.environ.get("TEMP", "/tmp")) / "STOP-HARMONY-WATCHER")
    parser.add_argument("--poll", type=int, default=30)
    parser.add_argument("--cooldown", type=int, default=60)
    parser.add_argument("--max-daily", type=int, default=20)
    parser.add_argument("--max-fail", type=int, default=3)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    if not args.enable:
        print("Watcher disabled. Direct delegate.py run remains available.")
        return 0
    if not args.allowed_root or min(args.poll, args.cooldown, args.max_daily, args.max_fail) < 1:
        parser.error("enable requires --allowed-root and positive limits")
    if args.kill_switch.exists():
        print("Kill switch present; refusing startup. It has not been removed.")
        return 1
    args.state_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = args.state_dir / "dispatched.json"
    lock = args.state_dir / "watcher.lock"
    try:
        lock_file = lock.open("x", encoding="utf-8")
    except FileExistsError:
        print("Watcher lock exists; inspect its owner before removing a stale lock.", file=sys.stderr)
        return 1
    failures = 0
    try:
        with lock_file:
            lock_file.write(json.dumps({"pid": os.getpid(), "started_at": now()}))
            lock_file.flush()
        while not args.kill_switch.exists():
            ledger = load_ledger(ledger_path)
            today = now()[:10]
            count = sum(1 for r in ledger.values() if r["claimed_at"].startswith(today))
            if count >= args.max_daily:
                print("Daily dispatch limit reached.")
                return 0
            result = dispatch_one(args.db, args.runs, ledger_path,
                                  args.allowed_root, args.allow_implement, args.kill_switch)
            if result is not None:
                print(json.dumps(result), flush=True)
                failures = 0 if result["status"] == "returned" else failures + 1
                if failures >= args.max_fail or result["status"] == "interrupted":
                    args.kill_switch.touch()
                    return 1
            if args.once:
                return 0
            deadline = time.monotonic() + (args.cooldown if result else args.poll)
            while time.monotonic() < deadline and not args.kill_switch.exists():
                time.sleep(0.2)
        return 0
    except KeyboardInterrupt:
        return 130
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
