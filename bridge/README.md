# Harmony delegation

Harmony is the durable coordination board. Claude Code is a separate worker.
Manual delegation remains the default; no service or watcher is installed or started.

## Direct delegation

Use Claude Code >= 2.1.295 and Python 3.13 with the existing Harmony dependencies from SETUP.md:

```powershell
$py = 'C:\Users\thepo\AppData\Local\Programs\Python\Python313\python.exe'
$bridge = 'C:\Users\thepo\OneDrive\Documents\GitHub\BMG-Harmony\bridge'
& $py "$bridge\delegate.py" doctor
& $py "$bridge\delegate.py" run 'C:\path\to\task.json'
& $py "$bridge\delegate.py" status 'unique-task-id'
& $py "$bridge\delegate.py" cancel 'unique-task-id'

```

A task is an explicit assignment, not permission to process arbitrary board history:

```json
{
  "version": 1,
  "task_id": "harmony-review-example",
  "objective": "Review bridge/delegate.py for correctness. Cite file locations and distinguish proved findings from uncertainty.",
  "workdir": "C:\\Users\\thepo\\OneDrive\\Documents\\GitHub\\BMG-Harmony",
  "mode": "review",
  "acceptance_criteria": [
    "Return actionable findings with evidence, or explain what was checked if none."
  ],
  "timeout_seconds": 600,
  "max_turns": 12
}
```

Use a fresh task_id for each assignment. The schema rejects unknown keys and invalid
limits. Objective, context, model, acceptance criteria and budgets travel with the task.
Claude receives the task once through UTF-8 stdin. No shell interprets the prompt.

The parent supervisor writes assignment/result records to a dedicated Harmony thread.
The worker has no board, shell, network-tool, app-control, or nested-agent tools.
The model service itself still uses network access; this is not offline inference.

## Implementation assignments

Use mode implement with allowed_files containing literal workspace-relative filenames,
e.g. ["src/parser.py", "tests/test_parser.py"]. No globs, directories, parent traversal,
Git metadata or agent-control files. Use forward slashes in these relative filenames.
The workspace must be a clean linked Git worktree (the primary checkout is refused). Prepare a separate worktree at
the intended commit, read its project instructions, and give its exact absolute path
as workdir. Dirty source work is never copied, reset or silently incorporated.

Only Read, Glob, Grep, Write and Edit are available. The PreToolUse guard checks resolved
paths and permits writes only to allowed_files. The parent runs builds/tests and
reviews the resulting diff, then integrates it under the target repo's own workflow.
Workers do not commit/push or receive Bash permission. If a task needs shell-driven
research, the parent can supply command output as context or perform those checks.

These are Claude tool/permission boundaries, not an OS filesystem or network sandbox.
Do not describe workdir, --add-dir or --allowedTools as a sandbox. --allowedTools
preapproves calls; --tools limits built-in tools. Explicit settings sources exclude
inherited settings/hooks/plugins; strict empty MCP config exposes no worker MCPs.
The task boundary hook uses exec-form arguments (no shell) and onFailure block;
unsupported older CLIs are rejected before model execution. Repository instructions remain relevant context.

## Results and acceptance

Local .harmony/runs/<task_id>/ contains task.json, prompt.txt, launch.json,
settings.json, mcp.json, boundary.py, stdout.json, stderr.log and state.json. These may contain
private task/code context and are git-ignored. Assignment and status receipts live
in the board's git-ignored SQLite store. They are durable local evidence.

States: created -> running -> returned, failed, blocked_auth, timed_out, cancelled,
or interrupted. A zero exit code plus a valid successful Claude result means returned.
It does not mean the criteria passed. Permission denials and session ID are retained.

After independently checking the criteria, record the decision and evidence:

```powershell
& $py "$bridge\delegate.py" verify 'unique-task-id' --accept --evidence 'Checked the cited lines and ran the targeted tests; results ...'
# Omit --accept to record rejection, still providing evidence.

```

Verification cannot silently overwrite a previous decision. Failed/timed-out/auth-blocked
runs cannot be accepted. Original stdout and status remain available. Treat model claims
as findings to verify, not project truth or human appearance/feel acceptance.

Cancellation is cooperative with the supervisor, which checks STOP every 100 ms.
Timeout/interruption kills the owned process tree. Windows uses a kill-on-close Job
Object, also reaping descendants when the supervisor exits/crashes. No detached
background worker is launched. Never kill unrelated Claude desktop sessions.

A run directory is created exclusively before launch. Crashed or failed tasks are not
automatically retried. Inspect artifacts, correct the cause, then assign a new task ID.
A crashed supervisor can leave a last-known running status: inspect it before any retry.

## Executable and authentication routing

Resolution: explicit --claude PATH, HARMONY_CLAUDE_EXE, native ~/.local/bin,
newest desktop-bundled CLI, then PATH. Npm shims resolve to Node's cli.js without
evaluating batch/PowerShell text. doctor reports the actual executable/version and
selected authentication fields, never tokens. Global options precede the subcommand.

Desktop-managed Claude Code sessions and a fresh standalone CLI need not share
authentication. An authenticated desktop session does not prove standalone CLI auth.
Changing executable selection does not copy credentials or attach to an active session.
Use the normal standalone claude auth login flow yourself if doctor reports none.
Do not extract desktop process tokens, edit credentials, or drive login UI.

The runner preserves normal subscription authentication; it does not use --bare,
which requires API-style authentication. It does not set an API key, install/update
Claude, modify home settings or change existing app sessions.

Claude Code runs tools locally and sends prompts and content it reads to its model
provider. This is the ordinary Claude Code data flow, not publishing the repository.
Confirm the user authorized Claude access to the chosen repository/task context.
A synthetic fixture can be used when private-code sharing is not authorized.

## Optional inbox watcher

Only envelopes with type harmony.delegation.task.v1 in harmony-delegations-claude,
posted as codex, are eligible. Old harmony-inbox-claude messages never execute.
Board attribution is not cryptographic authentication; this is a trusted local board.

```powershell
& $py "$bridge\delegate.py" submit 'C:\path\to\task.json'
& "$bridge\start-watcher.ps1" -Enable -AllowedRoot 'C:\exact\approved\worktree' -Once

```

Omit -Once only for an explicitly requested ongoing watcher. Implementation requires
-AllowImplement too. AllowedRoot matches exact resolved workspace roots, not their
parents. The default invocation is disabled. No startup registration is created.
Use a hidden background host only when authorized; direct delegation needs no daemon.

The watcher persists a claim before launch, acknowledges delivery separately, skips
invalid/ignored/dispatched heads, and never auto-replays after a crash. It has a singleton
lock, UTC daily cap, cooldown, failure cap and task timeouts. A malformed ledger fails
closed. Claims/failed assignments require inspection, not automatic retries.
A stale watcher.lock also requires checking its owner before deliberate removal.

The STOP-HARMONY-WATCHER file under TEMP blocks startup and cancels an active assignment.
The watcher never deletes this operator stop file. Delete it deliberately to re-enable.
Watcher ledger/lock state lives under .harmony/watcher/, not ephemeral prompt filenames.

## Compatibility and scope

claude-worker.ps1 accepts -TaskFile, or creates a one-off review from -Prompt/-PromptFile.
-OutputFormat text/json is supported. Old arbitrary -AllowedTools/-AllowBash grants are
rejected. Build/test commands belong to the supervisor.
start-watcher.ps1 no longer starts work without -Enable and explicit roots.

codex-conductor.ps1 is a legacy opt-in workflow, not the Claude delegation entry point.
It is not started by this setup. It retains a bounded workspace sandbox; missing
sentinels/failed runs halt and stop files are preserved. Blanket FullAccess is retired.

This repair does not claim completion of dormant debate/governance roadmap phases.

Sources: [hook execution and fail-closed behavior](https://code.claude.com/docs/en/hooks),
[programmatic Claude Code](https://code.claude.com/docs/en/headless),
[CLI reference](https://code.claude.com/docs/en/cli-reference).
