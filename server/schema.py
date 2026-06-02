"""
Event JSON Schema + validator for BMG-Harmony.

Exports:
    EVENT_SCHEMA  — JSON Schema Draft7 dict
    validate_event(event: dict) -> None  — raises jsonschema.ValidationError on invalid input
"""

from jsonschema import Draft7Validator

EVENT_SCHEMA: dict = {
    "type": "object",
    "required": ["event_id", "thread_id", "agent_id", "kind", "timestamp", "content_md"],
    "properties": {
        "event_id":     {"type": "string", "minLength": 1},
        "thread_id":    {"type": "string", "minLength": 1},
        "agent_id":     {"type": "string", "minLength": 1},
        "kind":         {"type": "string", "enum": ["message", "position", "dissent"]},
        "timestamp":    {"type": "string", "minLength": 1},
        "content_md":   {"type": "string"},
        "payload_json": {"type": ["string", "null"]},
    },
    "additionalProperties": False,
}

_validator = Draft7Validator(EVENT_SCHEMA)


def validate_event(event: dict) -> None:
    """Validate an event dict against EVENT_SCHEMA.

    Raises jsonschema.ValidationError on any schema violation.
    Returns None on success — never returns partial results.
    """
    _validator.validate(event)
