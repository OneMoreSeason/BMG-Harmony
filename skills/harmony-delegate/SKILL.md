---
name: harmony-delegate
description: Delegate a user-authorized, scoped task to Claude Code through BMG-Harmony, inspect its progress, and verify its result. Use when the user asks to hand work to Claude; ordinary coding does not authorize delegation.
---

Use BMG-Harmony at C:\Users\thepo\OneDrive\Documents\GitHub\BMG-Harmony.
Read bridge/README.md for operator commands and bridge/task.schema.json for the packet.

The user prefers choosing when to delegate and often works directly across two repos.
This skill does not grant standing permission to send private code to Claude or enable
watchers. Existing explicit assignment authority in the current session is sufficient;
do not ask again unless scope, destination or permissions materially change.

- Identify the recipient, repo/worktree, objective, allowed changes and acceptance
  criteria from the user's request. Claude Code sends its prompt and files it reads
  to its model provider. Keep context within the authorized repository/scope.
- Run bridge/delegate.py doctor to identify executable/auth routing. A desktop-managed
  Code session may be authenticated while standalone CLI auth is absent. Do not borrow
  process tokens, modify credentials, operate login UI or interrupt active sessions.
- Create an explicit version-1 task JSON with a unique task_id and absolute workdir.
  Default mode review. Implementation requires a clean separate Git worktree and
  literal allowed_files; the parent runs shell-based builds/tests and integration.
- Run directly through delegate.py run TASK_FILE. Capture its run_dir and task_id.
  CLI global options such as --claude/--runs/--db precede the subcommand.
- Read the actual result and diagnostics. returned is awaiting verification; failed,
  blocked_auth, timed_out and cancelled are not completion. Inspect citations/diffs
  and run the task's meaningful checks, then record verify with evidence.
- Report the worker's role, verified findings/changes, remaining uncertainty and receipt.
  Do not claim human appearance/feel acceptance. Neither a board ack nor Claude's own
  completion claim proves acceptance.
- No automatic retries or watchers. An interrupted run retains its artifacts and task ID;
  inspect before assigning a new task. cancel requests a stop for that owned run.

Use an isolated synthetic fixture when private-code transfer is not authorized.
Do not bypass an automatic approval rejection via a different launcher or tool.
