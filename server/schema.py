"""JSON Schemas and validators for BMG-Harmony."""

from jsonschema import Draft7Validator

EVENT_SCHEMA: dict = {
    "type": "object",
    "required": ["event_id", "thread_id", "agent_id", "kind", "timestamp", "content_md"],
    "properties": {
        "event_id": {"type": "string", "minLength": 1},
        "thread_id": {"type": "string", "minLength": 1},
        "agent_id": {"type": "string", "minLength": 1},
        "kind": {"type": "string", "enum": ["message", "position", "dissent"]},
        "timestamp": {"type": "string", "minLength": 1},
        "content_md": {"type": "string"},
        "payload_json": {"type": ["string", "null"]},
        "parent_event_id": {"type": ["string", "null"], "minLength": 1},
    },
    "additionalProperties": False,
}

ACK_SCHEMA: dict = {
    "type": "object",
    "required": ["ack_id", "message_id", "agent_id", "delivered_at"],
    "properties": {
        "ack_id": {"type": "string", "minLength": 1},
        "message_id": {"type": "string", "minLength": 1},
        "agent_id": {"type": "string", "minLength": 1},
        "delivered_at": {"type": "string", "minLength": 1},
    },
    "additionalProperties": False,
}

PROVING_ENVELOPE_SCHEMA: dict = {
    "type": "object",
    "required": [
        "envelope_id",
        "thread_id",
        "agent_id",
        "timestamp",
        "proved",
        "not_checked",
        "confidence",
    ],
    "properties": {
        "envelope_id": {"type": "string", "minLength": 1},
        "thread_id": {"type": "string", "minLength": 1},
        "agent_id": {"type": "string", "minLength": 1},
        "timestamp": {"type": "string", "minLength": 1},
        "proved": {"type": "string"},
        "not_checked": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    },
    "additionalProperties": False,
}

_event_validator = Draft7Validator(EVENT_SCHEMA)
_ack_validator = Draft7Validator(ACK_SCHEMA)
_proving_envelope_validator = Draft7Validator(PROVING_ENVELOPE_SCHEMA)


def validate_event(event: dict) -> None:
    """Validate an event dict against EVENT_SCHEMA."""
    _event_validator.validate(event)


def validate_ack(ack: dict) -> None:
    """Validate an ack dict against ACK_SCHEMA."""
    _ack_validator.validate(ack)


def validate_proving_envelope(envelope: dict) -> None:
    """Validate an envelope dict against PROVING_ENVELOPE_SCHEMA."""
    _proving_envelope_validator.validate(envelope)
