"""Delegation behavior tests: owned board/workspaces and real child processes."""
import importlib.util
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

BRIDGE = Path(__file__).resolve().parents[1] / "bridge"
sys.path.insert(0, str(BRIDGE))
import delegate
import guard
from server.store import init_db, read_thread, write_event

spec = importlib.util.spec_from_file_location("watcher", BRIDGE / "harmony-inbox-watcher.py")
watcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watcher)


@pytest.fixture
def task(tmp_path):
    work = tmp_path / "workspace"
    work.mkdir()
    (work / "evidence.txt").write_text("owned evidence")
    return {"version": 1, "task_id": "owned-task", "objective": "Inspect evidence.txt",
            "workdir": str(work), "mode": "review",
            "acceptance_criteria": ["Cite owned evidence"], "timeout_seconds": 3}


@pytest.fixture
def fake(tmp_path):
    path = tmp_path / "fake worker.py"
    path.write_text(
        "import json,sys,time,subprocess\n"
        "from pathlib import Path\n"
        "if '--version' in sys.argv: print('2.1.309 (owned fixture)');sys.exit(0)\n"
        "text=sys.stdin.read()\n"
        "task=json.loads(text.split('TASK_DATA_START\\n',1)[1].split('\\nTASK_DATA_END',1)[0])\n"
        "mode=task.get('context','')\n"
        "if mode=='sleep': time.sleep(30)\n"
        "if mode=='tree':\n"
        " child=subprocess.Popen([sys.executable,'-c',"
        "'import time;from pathlib import Path;"
        "p=Path('+repr(task['workdir']+'/child-heartbeat')+');"
        "exec(\"while True:\\\\n p.write_text(str(time.time()))\\\\n time.sleep(.05)\")'])\n"
        " time.sleep(30)\n"
        "if mode=='invalid': print('not JSON');sys.exit(0)\n"
        "if mode=='nonzero': print('{}');sys.exit(7)\n"
        "print('owned diagnostic',file=sys.stderr)\n"
        "print(json.dumps({'type':'result','is_error':mode=='auth',"
        "'session_id':'owned-session','result':'Not logged in' if mode=='auth' else 'owned evidence',"
        "'permission_denials':[]}))\n",
        encoding="utf-8")
    return [sys.executable, str(path)]


def run(task, tmp_path, fake):
    return delegate.run_task(task, tmp_path / "runs", tmp_path / "board.sqlite", fake)


@pytest.mark.parametrize("field,value", [
    ("task_id", "../escape"), ("mode", "unbounded"), ("timeout_seconds", 0),
    ("max_turns", 0), ("version", 2), ("acceptance_criteria", []),
    ("unexpected", True), ("model", "opus;echo leak"),
])
def test_bad_packet_rejected(task, field, value):
    task[field] = value
    with pytest.raises(Exception):
        delegate.validate_task(task)


@pytest.mark.parametrize("path", ["../escape", "/absolute", ".git/config",
                                   ".claude/settings.json", "*.py", ".", "a\\b"])
def test_bad_write_paths_rejected(task, path):
    task.update(mode="implement", allowed_files=[path])
    with pytest.raises(Exception):
        delegate.validate_task(task)


def test_review_cannot_request_writes(task):
    task["allowed_files"] = ["evidence.txt"]
    with pytest.raises(ValueError):
        delegate.validate_task(task)


def test_implementation_needs_files_and_clean_git(task, tmp_path, fake):
    task["mode"] = "implement"
    with pytest.raises(ValueError):
        delegate.validate_task(task)
    task["allowed_files"] = ["evidence.txt"]
    with pytest.raises(ValueError, match="Git"):
        run(task, tmp_path, fake)


@pytest.mark.parametrize("name,path,ok", [
    ("Read", "evidence.txt", True), ("Read", "../outside", False),
    ("Write", "evidence.txt", False), ("Bash", "", False),
    ("Agent", "", False), ("Read", ".git/config", False),
    ("Grep", ".", True), ("Glob", ".", True),
    ("Read", ".claude/settings.json", False),
])
def test_review_guard(task, name, path, ok):
    event = {"tool_name": name, "tool_input": {
        "file_path": path, "path": path}}
    assert guard.check(task, event)[0] is ok


def test_implementation_guard_exact_files(task):
    task.update(mode="implement", allowed_files=["evidence.txt"])
    assert guard.check(task, {"tool_name": "Edit",
                             "tool_input": {"file_path": "evidence.txt"}})[0]
    assert not guard.check(task, {"tool_name": "Edit",
                                 "tool_input": {"file_path": "other.txt"}})[0]


def test_real_guard_protocol(task, tmp_path):
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps(task))
    event = json.dumps({"tool_name": "Write", "tool_input": {"file_path": "evidence.txt"}})
    p = subprocess.run([sys.executable, str(BRIDGE / "guard.py"), str(policy)],
                       input=event, capture_output=True, text=True)
    assert p.returncode == 2
    assert "explicit" in p.stderr
    p = subprocess.run([sys.executable, str(BRIDGE / "guard.py"), str(policy)],
                       input="malformed", capture_output=True, text=True)
    assert p.returncode == 2


def test_launch_has_explicit_tool_and_settings_boundary(task, tmp_path):
    directory = tmp_path / "run"
    directory.mkdir()
    command = delegate.build_command(["claude.exe"], delegate.validate_task(task), directory)
    assert command[command.index("--tools") + 1] == "Read,Glob,Grep"
    assert command[command.index("--setting-sources") + 1] == ""
    assert "--strict-mcp-config" in command
    assert "--dangerously-skip-permissions" not in command
    assert "--bare" not in command  # subscription auth is intentionally preserved
    assert json.loads((directory / "mcp.json").read_text()) == {"mcpServers": {}}
    settings = json.loads((directory / "settings.json").read_text())
    assert settings["permissions"]["defaultMode"] == "dontAsk"
    hook = settings["hooks"]["PreToolUse"][0]["hooks"][0]
    assert hook["command"] == sys.executable
    assert Path(hook["args"][0]).name == "boundary.py"
    assert Path(hook["args"][0]).read_bytes() == (BRIDGE / "guard.py").read_bytes()
    assert hook["onFailure"] == "block"


def test_success_is_returned_not_accepted(task, tmp_path, fake):
    result = run(task, tmp_path, fake)
    assert result["status"] == "returned"
    assert result["verification"] == "pending"
    assert result["session_id"] == "owned-session"
    assert result["result"] == "owned evidence"
    directory = Path(result["run_dir"])
    assert (directory / "stdout.json").exists()
    assert "owned diagnostic" in (directory / "stderr.log").read_text()
    con = init_db(str(tmp_path / "board.sqlite"))
    events = read_thread(con, "harmony-task-owned-task")
    con.close()
    assert [json.loads(e["payload_json"])["type"] for e in events] == [
        "harmony.delegation.assigned.v1", "harmony.delegation.returned.v1"]
    accepted = delegate.verify_run(directory, True, "Supervisor checked owned evidence",
                                   tmp_path / "board.sqlite")
    assert accepted["verification"] == "accepted"
    with pytest.raises(ValueError, match="already"):
        delegate.verify_run(directory, True, "again", tmp_path / "board.sqlite")


def test_duplicate_run_never_replays(task, tmp_path, fake):
    run(task, tmp_path, fake)
    with pytest.raises(FileExistsError):
        run(task, tmp_path, fake)


@pytest.mark.parametrize("context,expected", [
    ("auth", "blocked_auth"), ("invalid", "failed"), ("nonzero", "failed"),
    ("sleep", "timed_out"),
])
def test_failures_do_not_look_complete(task, tmp_path, fake, context, expected):
    task.update(context=context, timeout_seconds=1)
    state = run(task, tmp_path, fake)
    assert state["status"] == expected
    assert state["verification"] == "pending"
    with pytest.raises(ValueError, match="Only a returned"):
        delegate.verify_run(state["run_dir"], True, "not enough", tmp_path / "board.sqlite")


def test_active_cancellation(task, tmp_path, fake):
    task.update(context="sleep", timeout_seconds=20)
    result = {}
    thread = threading.Thread(target=lambda: result.update(run(task, tmp_path, fake)))
    thread.start()
    directory = tmp_path / "runs/owned-task"
    deadline = time.monotonic() + 5
    while not (directory / "state.json").exists() and time.monotonic() < deadline:
        time.sleep(.01)
    (directory / "STOP").touch()
    thread.join(timeout=5)
    assert not thread.is_alive()
    assert result["status"] == "cancelled"


def test_timeout_reaps_descendant(task, tmp_path, fake):
    task.update(context="tree", timeout_seconds=2)
    state = run(task, tmp_path, fake)
    assert state["status"] == "timed_out"
    heartbeat = Path(task["workdir"]) / "child-heartbeat"
    assert heartbeat.exists(), (Path(state["run_dir"]) / "stderr.log").read_text()
    stamp = heartbeat.read_text()
    time.sleep(.3)
    assert heartbeat.read_text() == stamp


def post(db, payload, agent="codex", thread=watcher.INBOX_THREAD):
    con = init_db(str(db))
    result = write_event(con, {"thread_id": thread, "agent_id": agent, "kind": "message",
                              "content_md": "owned fixture", "payload_json": json.dumps(payload)})
    con.close()
    return result["event_id"]


def test_watcher_skips_bad_and_already_dispatched_heads(task, tmp_path):
    db = tmp_path / "board.sqlite"
    post(db, {"type": "old-chat"})
    post(db, {"type": "harmony.delegation.task.v1", "task": task}, agent="claude")
    first = post(db, {"type": "harmony.delegation.task.v1", "task": task})
    second = post(db, {"type": "harmony.delegation.task.v1", "task": task})
    assert watcher.poll_inbox(db, {})[0] == first
    assert watcher.poll_inbox(db, {first: {"status": "claimed"}})[0] == second


def test_legacy_inbox_is_never_executable(task, tmp_path):
    db = tmp_path / "board.sqlite"
    post(db, {"type": "harmony.delegation.task.v1", "task": task},
         thread="harmony-inbox-claude")
    assert watcher.poll_inbox(db, {}) is None


def test_watcher_requires_exact_root_and_explicit_implementation(task):
    with pytest.raises(ValueError, match="root"):
        watcher.allowed_task(task, [str(Path(task["workdir"]).parent)])
    task.update(mode="implement", allowed_files=["evidence.txt"])
    with pytest.raises(ValueError, match="implementation"):
        watcher.allowed_task(task, [task["workdir"]])
    assert watcher.allowed_task(task, [task["workdir"]], True)["mode"] == "implement"


def test_watcher_disabled_and_kill_switch_preserved(tmp_path):
    assert watcher.main([]) == 0
    stop = tmp_path / "STOP"
    stop.touch()
    assert watcher.main(["--enable", "--allowed-root", str(tmp_path),
                         "--kill-switch", str(stop)]) == 1
    assert stop.exists()


def test_bad_ledger_does_not_silently_replay(tmp_path):
    path = tmp_path / "ledger.json"
    path.write_text("broken")
    with pytest.raises(ValueError):
        watcher.load_ledger(path)


def test_rejected_task_does_not_starve_next(task, tmp_path, monkeypatch):
    db = tmp_path / "board.sqlite"
    bad = {**task, "task_id": "../escape"}
    first = post(db, {"type": "harmony.delegation.task.v1", "task": bad})
    second = post(db, {"type": "harmony.delegation.task.v1", "task": task})
    ledger = tmp_path / "ledger.json"
    monkeypatch.setattr(watcher, "run_task", lambda *a, **kw: {"status": "returned"})
    assert watcher.dispatch_one(db, tmp_path / "runs", ledger,
                                [task["workdir"]])["status"] == "rejected"
    assert watcher.dispatch_one(db, tmp_path / "runs", ledger,
                                [task["workdir"]])["status"] == "returned"
    saved = watcher.load_ledger(ledger)
    assert saved[first]["status"] == "rejected"
    assert saved[second]["status"] == "returned"


def test_crashed_claim_is_not_replayed(task, tmp_path, monkeypatch):
    db = tmp_path / "board.sqlite"
    event = post(db, {"type": "harmony.delegation.task.v1", "task": task})
    ledger = tmp_path / "ledger.json"
    def crash(*args, **kwargs):
        raise KeyboardInterrupt()
    monkeypatch.setattr(watcher, "run_task", crash)
    with pytest.raises(KeyboardInterrupt):
        watcher.dispatch_one(db, tmp_path / "runs", ledger, [task["workdir"]])
    assert watcher.load_ledger(ledger)[event]["status"] == "claimed"
    assert watcher.poll_inbox(db, watcher.load_ledger(ledger)) is None


def test_version_gate_rejects_unsupported_without_model(task, tmp_path):
    old = tmp_path / "old.py"
    old.write_text("print('2.1.161 (old fixture)')")
    result = delegate.run_task(task, tmp_path / "runs", tmp_path / "board.sqlite",
                               [sys.executable, str(old)])
    assert result["status"] == "failed"
    assert "2.1.295" in result["error"]
    assert not (Path(result["run_dir"]) / "launch.json").exists()


def test_large_prompt_is_delivered_once_without_pipe_block(task, tmp_path, fake):
    task["context"] = "x" * 32000
    task["objective"] = "y" * 16000
    state = run(task, tmp_path, fake)
    assert state["status"] == "returned"
    prompt = (Path(state["run_dir"]) / "prompt.txt").read_text()
    assert prompt.count("y" * 16000) == 1


def test_watcher_malformed_array_payload_is_skipped(task, tmp_path):
    db = tmp_path / "board.sqlite"
    post(db, ["not", "an", "envelope"])
    expected = post(db, {"type": "harmony.delegation.task.v1", "task": task})
    assert watcher.poll_inbox(db, {})[0] == expected


def test_watcher_stop_cancels_owned_worker(task, tmp_path, fake):
    task.update(context="sleep", timeout_seconds=20)
    stop = tmp_path / "watcher-stop"
    result = {}
    thread = threading.Thread(target=lambda: result.update(delegate.run_task(
        task, tmp_path / "runs", tmp_path / "board.sqlite", fake, cancel_file=stop)))
    thread.start()
    deadline = time.monotonic() + 5
    while not (tmp_path / "runs/owned-task/state.json").exists() and time.monotonic() < deadline:
        time.sleep(.01)
    stop.touch()
    thread.join(timeout=5)
    assert not thread.is_alive()
    assert result["status"] == "cancelled"


def test_model_failure_cannot_be_accepted_with_empty_evidence(task, tmp_path, fake):
    state = run(task, tmp_path, fake)
    with pytest.raises(ValueError, match="evidence"):
        delegate.verify_run(state["run_dir"], True, " ", tmp_path / "board.sqlite")


def test_safe_node_shim_resolution_never_evaluates_shell(tmp_path):
    shim = tmp_path / "claude.cmd"
    shim.write_text("echo do not execute this")
    entry = tmp_path / "node_modules/@anthropic-ai/claude-code/cli.js"
    entry.parent.mkdir(parents=True)
    entry.write_text("/* owned test */")
    command = delegate.command_for(shim)
    assert Path(command[0]).stem.lower() == "node"
    assert Path(command[1]) == entry
    assert "cmd.exe" not in command


def test_direct_child_exit_reaps_lingering_descendant(task, tmp_path):
    helper = tmp_path / "exit-helper.py"
    heartbeat = str(Path(task["workdir"]) / "lingering")
    code = ("import time;from pathlib import Path;p=Path(" + repr(heartbeat)
            + ");exec('while True:\\n p.write_text(str(time.time()))\\n time.sleep(.05)')")
    helper.write_text(
        "import subprocess,sys,time,json\n"
        "if '--version' in sys.argv: print('2.1.309');sys.exit(0)\n"
        "sys.stdin.read()\n"
        "subprocess.Popen([sys.executable,'-c'," + repr(code) + "])\n"
        "time.sleep(.3)\n"
        "print(json.dumps({'type':'result','is_error':False,'result':'done'}))\n")
    state = run(task, tmp_path, [sys.executable, str(helper)])
    assert state["status"] == "returned"
    marker = Path(heartbeat)
    assert marker.exists()
    stamp = marker.read_text()
    time.sleep(.2)
    assert marker.read_text() == stamp


def test_implementation_refuses_primary_checkout(task, tmp_path, fake):
    work = task["workdir"]
    subprocess.run(["git", "-C", work, "init", "-q"], check=True)
    subprocess.run(["git", "-C", work, "add", "evidence.txt"], check=True)
    subprocess.run(["git", "-C", work, "-c", "user.name=Owned Test",
                    "-c", "user.email=owned@example.invalid", "commit", "-qm", "fixture"], check=True)
    task.update(mode="implement", allowed_files=["evidence.txt"])
    with pytest.raises(ValueError, match="linked"):
        run(task, tmp_path, fake)


def test_implementation_runs_in_owned_linked_worktree(task, tmp_path, fake):
    source = task["workdir"]
    subprocess.run(["git", "-C", source, "init", "-q"], check=True)
    subprocess.run(["git", "-C", source, "add", "evidence.txt"], check=True)
    subprocess.run(["git", "-C", source, "-c", "user.name=Owned Test",
                    "-c", "user.email=owned@example.invalid", "commit", "-qm", "fixture"], check=True)
    work = tmp_path / "linked"
    subprocess.run(["git", "-C", source, "worktree", "add", "--detach", str(work)],
                   check=True, capture_output=True)
    task.update(workdir=str(work), mode="implement", allowed_files=["evidence.txt"])
    state = run(task, tmp_path, fake)
    assert state["status"] == "returned"
    assert state["workspace_status_after"] == ""
    launch = json.loads((Path(state["run_dir"]) / "launch.json").read_text())
    args = launch["command"]
    assert args[args.index("--tools") + 1] == "Read,Glob,Grep,Write,Edit"


def test_verification_lock_prevents_concurrent_decisions(task, tmp_path, fake):
    state = run(task, tmp_path, fake)
    directory = Path(state["run_dir"])
    (directory / "verification.lock").write_text("owned active supervisor")
    with pytest.raises(ValueError, match="in progress"):
        delegate.verify_run(directory, True, "evidence", tmp_path / "board.sqlite")
    assert json.loads((directory / "state.json").read_text())["verification"] == "pending"
