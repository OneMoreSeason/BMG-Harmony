-- BMG-Harmony canonical schema
-- Committed to git as the DDL source of truth.
-- Executed via con.executescript() in init_db().

PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS threads (
    thread_id  TEXT PRIMARY KEY,
    slug       TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    state      TEXT NOT NULL DEFAULT 'open'
);

CREATE TABLE IF NOT EXISTS events (
    event_id     TEXT PRIMARY KEY,
    thread_id    TEXT NOT NULL REFERENCES threads(thread_id),
    agent_id     TEXT NOT NULL,
    kind         TEXT NOT NULL,
    timestamp    TEXT NOT NULL,
    content_md   TEXT NOT NULL,
    payload_json TEXT
);

CREATE TRIGGER IF NOT EXISTS prevent_event_update
BEFORE UPDATE ON events
BEGIN
    SELECT RAISE(ABORT, 'events are immutable');
END;

CREATE TRIGGER IF NOT EXISTS prevent_event_delete
BEFORE DELETE ON events
BEGIN
    SELECT RAISE(ABORT, 'events cannot be deleted');
END;
