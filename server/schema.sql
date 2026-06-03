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
    event_id        TEXT PRIMARY KEY,
    thread_id       TEXT NOT NULL REFERENCES threads(thread_id),
    agent_id        TEXT NOT NULL,
    kind            TEXT NOT NULL,
    timestamp       TEXT NOT NULL,
    content_md      TEXT NOT NULL,
    payload_json    TEXT,
    parent_event_id TEXT REFERENCES events(event_id)
);

CREATE TABLE IF NOT EXISTS message_acks (
    ack_id       TEXT PRIMARY KEY,
    message_id   TEXT NOT NULL REFERENCES events(event_id),
    agent_id     TEXT NOT NULL,
    delivered_at TEXT NOT NULL,
    UNIQUE(message_id, agent_id)
);

CREATE TABLE IF NOT EXISTS proving_envelopes (
    envelope_id TEXT PRIMARY KEY,
    thread_id   TEXT NOT NULL REFERENCES threads(thread_id),
    agent_id    TEXT NOT NULL,
    timestamp   TEXT NOT NULL,
    proved      TEXT NOT NULL,
    not_checked TEXT NOT NULL,
    confidence  REAL NOT NULL CHECK(confidence >= 0.0 AND confidence <= 1.0)
);

CREATE TABLE IF NOT EXISTS role_definitions (
    agent_id               TEXT PRIMARY KEY,
    role_md                TEXT NOT NULL,
    authority_domains_json TEXT NOT NULL,
    default_route_for_json TEXT NOT NULL,
    created_at             TEXT NOT NULL
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

CREATE TRIGGER IF NOT EXISTS prevent_ack_update
BEFORE UPDATE ON message_acks
BEGIN
    SELECT RAISE(ABORT, 'message acknowledgements are immutable');
END;

CREATE TRIGGER IF NOT EXISTS prevent_ack_delete
BEFORE DELETE ON message_acks
BEGIN
    SELECT RAISE(ABORT, 'message acknowledgements cannot be deleted');
END;

CREATE TRIGGER IF NOT EXISTS prevent_proving_envelope_update
BEFORE UPDATE ON proving_envelopes
BEGIN
    SELECT RAISE(ABORT, 'proving envelopes are immutable');
END;

CREATE TRIGGER IF NOT EXISTS prevent_proving_envelope_delete
BEFORE DELETE ON proving_envelopes
BEGIN
    SELECT RAISE(ABORT, 'proving envelopes cannot be deleted');
END;

CREATE TRIGGER IF NOT EXISTS prevent_role_definition_update
BEFORE UPDATE ON role_definitions
BEGIN
    SELECT RAISE(ABORT, 'role definitions are immutable in Phase 2');
END;

CREATE TRIGGER IF NOT EXISTS prevent_role_definition_delete
BEFORE DELETE ON role_definitions
BEGIN
    SELECT RAISE(ABORT, 'role definitions cannot be deleted in Phase 2');
END;
