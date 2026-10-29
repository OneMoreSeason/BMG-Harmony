---
status: incomplete
date: 2026-10-29
quick_id: 261029-pkr
verification: local-passed-live-pending
---
# Formal Claude delegation: local repair complete, live round trip pending

## Outcome
Implemented an explicit Claude Code supervisor and formal task contract. No watcher
or ongoing automation was enabled. User-directed manual delegation remains available.

- Validated task IDs, objectives, workspace, mode, file list and acceptance criteria.
- Read-only default; implementation requires a clean linked Git worktree and exact
  writable filenames. No worker Bash, app control, worker MCPs or nested agents.
- Fresh explicit settings, exec-form fail-closed boundary hooks, immutable per-run
  guard snapshot, and Claude Code >= 2.1.295 requirement.
- JSON task/run artifacts, unique durable task IDs, separate worker return and
  supervisor acceptance/rejection, and a verification lock.
- Bounded runtime/turns, cancellation and Windows kill-on-close process-tree ownership.
- Formal-envelope-only opt-in watcher with exact allowed roots, queue progress,
  durable pre-launch claims, stop preservation, daily/failure caps and singleton lock.
- Compatibility PowerShell commands retained with explicit safer semantics.
- Legacy conductor refuses FullAccess, preserves stops, halts on nonzero/missing
  final evidence, and never treats echoed prompt/stderr sentinels as completion.
- Reusable harmony-delegate skill packaged and installed, with matching source hash.

## Authority and alignment
User explicitly requested repairing Harmony and formalizing delegation in the OMSv4
chat on 2026-10-29. Reveille agent-control-surface route and BMG-Brain profile loaded.
Learned lesson: delivery acknowledgment and a worker's own claim are not acceptance.
BMG coordinates; target repositories own truth; tools/memory are context.

Chat cwd: C:/Users/thepo/OneDrive/Documents/GitHub/OMSv4.
Implementation Git root: C:/Users/thepo/OneDrive/Documents/GitHub/BMG-Harmony.
Clean baseline main c7a9a6f; scoped Git metadata write probe passed before mutation.
Original staging was empty. No OMSv4, LMG3 or running Claude app sessions were edited.
Only two new home skill files were installed; credentials/home settings were not edited.

## Verification
- Baseline: 46 tests passed.
- Final: 103 tests passed in 17.31 seconds (46 retained + 57 delegation tests).
- Real owned subprocess fixtures exercise success/failure/auth-style errors,
  malformed output, large prompt delivery, cancellation, timeout, lingering
  descendant cleanup, task duplication, guard denials, linked-worktree gating,
  independent verification, queue starvation/recovery, and conductor sentinels.
- All three PowerShell entry points parse.
- start-watcher.ps1 -Once prints disabled and returns without starting a watcher.
- Python compileall and skill quick_validate pass.
- Installed skill source/readback SHA256:
  2D37CDB2122534FD61BFFB8873ABC29C45C89C6240AA717E0B23EEED78799101.
- Actual connected Harmony MCP status write/read:
  thread harmony-delegation-maintenance-261029,
  event 01a189d0-428d-7ac0-81b7-09045e3c846d, revision 213.
  This was a maintenance status, not a task sent to Claude.
- Diff review caught and corrected a locale-dependent text conversion before
  publication. server/harmony_server.py is byte-restored to baseline.

## Not proved / blocked
No live Claude model worker ran. The attempted read-only Harmony review was rejected
before process launch by automatic approval review: it considered access to private
Harmony content by an external Claude worker insufficiently explicit. The user asked
why data would go to Anthropic; the model-service data flow was explained. That reply
was clarification, not approval. No alternate launcher was used to bypass rejection.

Standalone doctor selects desktop-bundled Claude Code 2.1.309, versus old npm 2.1.161.
Fresh standalone auth reports none at C:/Users/thepo/.claude. The user's app-managed
Code sessions are active; this is a separate authentication context, not a claim
that the user is logged out of Claude. No process tokens were read or copied.

Remaining: explicit scope approval for a live private-code test (or synthetic-only
test), usable standalone authentication, then a bounded real worker/guard round trip.
OS sandbox isolation and roadmap debate/governance phases are not claimed.

## Git and closeout
Runtime commits: 63fd7c4 (delegation), 47d37f9 (encoding restoration),
e259f59 (final completion evidence). Documentation/skill/state commit follows.
Pull-before-push and final origin/main readback are required. Publication was rejected before process launch by automatic approval review:
explicit approval is required for https://github.com/OneMoreSeason/BMG-Harmony.git,
branch main. No pull/push ran. See PUBLISH.md for both approval rejections and the
required next action. All work remains committed locally; external closeout is
INCOMPLETE.

## Next use
Read bridge/README.md or invoke the installed harmony-delegate skill for an explicitly
authorized task. Run doctor before trusting executable/auth context. Create a new task
ID, use direct run, inspect actual artifacts and verify with evidence. Never restart
a watcher or replay historical inbox work merely because this setup now exists.
