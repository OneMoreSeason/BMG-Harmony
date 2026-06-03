---
phase: 02-full-board-battle-cards-roles
plan: "01"
subsystem: store
tags: [sqlite, board, ack, replies, migration]
requirements_completed: [BOARD-03, BOARD-04, BOARD-05]
status: complete
completed: 2026-06-03
---

# Phase 2 Plan 01 Summary: Board Mechanics

## Accomplishments

- Added Phase 2 schema for structural replies and delivery proof:
  - `events.parent_event_id`
  - `message_acks`
  - append-only ack triggers
- Added idempotent migration in `init_db` so Phase 1 stores gain
  `parent_event_id` without losing existing events.
- Added `ack_message` with idempotent re-ack behavior.
- Added `reply_message` with same-thread parent validation.
- Enriched `read_thread` rows with `parent_event_id` and `acks`.
- Preserved `list_threads(state?)` compatibility.

## Files Changed

- `server/schema.sql`
- `server/schema.py`
- `server/store.py`
- `tests/test_store.py`
- `tests/test_phase2_board.py`

## Validation

- `python -m pytest tests/test_store.py tests/test_phase2_board.py tests/test_phase2_battle_card.py -v`
- Result: 17 passed during focused store/card validation.
- Full-suite validation later passed 19/19 in Plan 03.

## Notes

No live `.harmony/store/harmony.sqlite` dogfood mutation was performed in this
plan. Tests use temp SQLite stores only.
