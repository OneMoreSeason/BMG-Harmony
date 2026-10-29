---
status: in-progress
date: 2026-10-29
quick_id: 261029-pkr
---
# Repair Harmony and formalize explicit Claude delegation

Authority: user request in the existing OMSv4 chat, 2026-10-29. Route:
BMG-Brain/docs/routes/agent-control-surface.md; profile BMG-Brain.
Implementation owner: BMG-Harmony. Current chat cwd is OMSv4. Harmony Git root
was verified and a temporary Git metadata write probe succeeded; no OMSv4 changes.

Invariant ledger: BMG coordinates; target repositories own truth; memory/tools
are context; acknowledgment is delivery only; worker return needs supervisor
verification. Manual user delegation remains available and automatic watchers
remain opt-in. No active Claude desktop sessions, home credentials, app controls,
or product repositories are modified.

1. Replace the fragile worker launch with a bounded supervisor: validated task
   packets, read-only default, explicit file-scoped implementation, isolated
   settings/MCP exposure, structured artifacts, task/run IDs, cancellation,
   process-tree cleanup, and separate verification/acceptance.
2. Repair watcher queue progress and crash deduplication. Only formal new task
   envelopes are executable; legacy chatter/backlog is not authority to run.
   Keep kill switches and runtime/daily caps, default watcher off.
3. Retain documented compatibility entry points, correct obsolete safety/setup
   claims, provide task examples and operator commands.
4. Validate real subprocess lifecycle, tool guards, permissions/arguments, queue
   behavior, duplicate prevention and board round trips using owned fixtures.
   Existing baseline: 46 tests pass. Attempt a real Claude round trip using the
   actual available authentication; never borrow live app session credentials.
5. Record summary/verification and STATE.md quick-task row; meaningful scoped
   commits, pull-before-push and push receipt, or explicit incomplete receipt.

Known routing evidence: npm CLI 2.1.161; desktop-bundled CLI 2.1.309. User is
actively logged in to app-managed Code sessions. Fresh standalone auth checks
for both binaries report none at ~/.claude. This is a context distinction,
not evidence that the user is logged out of Claude.
