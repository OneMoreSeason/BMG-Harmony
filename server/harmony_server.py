"""
BMG-Harmony MCP server entrypoint.

Exposes four FastMCP tools for the shared agent coordination board:
  - post_message        — post an attributed message to a named thread
  - read_thread         — return full message history for a thread
  - list_threads        — list all threads (optional state filter)
  - post_stack_position — convenience wrapper: post kind=position to harmony-stack-decision

Logging is directed exclusively to sys.stderr.
stdout is owned by the FastMCP stdio transport (JSON-RPC wire protocol).
Any write to stdout outside FastMCP will corrupt the MCP connection.
"""

# ---------------------------------------------------------------------------
# Logging setup — MUST be first, before any other import that might configure
# the root logger or emit output.
# ---------------------------------------------------------------------------
import sys
import logging

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("harmony_server")

# ---------------------------------------------------------------------------
# Standard library imports
# ---------------------------------------------------------------------------
import json
import os
from contextlib import asynccontextmanager

# ---------------------------------------------------------------------------
# MCP imports
# ---------------------------------------------------------------------------
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError  # verified: mcp 1.27.x

# ---------------------------------------------------------------------------
# Store layer imports
# ---------------------------------------------------------------------------
from server.store import (
    init_db,
    write_event,
    read_thread as _read_thread,
    list_threads as _list_threads,
)

# ---------------------------------------------------------------------------
# Module-level DB connection — opened once in lifespan, used by all tools.
# ---------------------------------------------------------------------------
_db = None


# ---------------------------------------------------------------------------
# FastMCP lifespan — open/close the SQLite store once per server process.
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(server):
    global _db
    db_path = os.environ.get("HARMONY_DB_PATH")
    if not db_path:
        logger.error(
            "HARMONY_DB_PATH environment variable is not set — cannot start server"
        )
        raise RuntimeError(
            "HARMONY_DB_PATH environment variable is not set. "
            "Set it to the absolute path of the SQLite store file before starting the server."
        )
    logger.info("Opening store at %s", db_path)
    _db = init_db(db_path)
    try:
        yield {"db": _db}
    finally:
        logger.info("Closing store")
        _db.close()
        _db = None


# ---------------------------------------------------------------------------
# FastMCP instance
# ---------------------------------------------------------------------------
mcp = FastMCP("bmg-harmony", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def post_message(
    thread_id: str,
    agent_id: str,
    kind: str,
    content_md: str,
    payload_json: str | None = None,
) -> dict:
    """Post an attributed message to a named thread.

    Returns event receipt with event_id, thread_id, revision, timestamp,
    validation_status. Threads are auto-created on first post. Raises ToolError
    if required fields are invalid or the kind value is not one of: message,
    position, dissent.
    """
    return write_event(
        _db,
        {
            "thread_id": thread_id,
            "agent_id": agent_id,
            "kind": kind,
            "content_md": content_md,
            "payload_json": payload_json,
        },
    )


@mcp.tool()
def read_thread(thread_id: str) -> dict:
    """Return full message history for a thread in insertion order.

    Returns a dict with keys: thread_id (str), events (list of event dicts).
    Each event dict has keys: event_id, thread_id, agent_id, kind, timestamp,
    content_md, payload_json. Returns empty events list if thread does not exist.
    """
    return {"thread_id": thread_id, "events": _read_thread(_db, thread_id)}


@mcp.tool()
def list_threads(state: str | None = None) -> dict:
    """List all threads and their current state.

    Optionally filter by state (e.g. 'open'). Returns a dict with key
    'threads' — a list of dicts each containing: thread_id, slug,
    created_at, state.
    """
    return {"threads": _list_threads(_db, state)}


@mcp.tool()
def post_stack_position(
    agent_id: str,
    position_md: str,
    objections: str | None = None,
) -> dict:
    """Post an explicit stack or design position to the shared decision thread.

    Posts to the well-known thread 'harmony-stack-decision' with kind=position.
    If objections is provided, it is stored as a JSON payload string
    {"objections": "<text>"}. Returns the same receipt shape as post_message:
    event_id, thread_id, revision, timestamp, validation_status.
    """
    payload = None
    if objections is not None:
        payload = json.dumps({"objections": objections})

    return write_event(
        _db,
        {
            "thread_id": "harmony-stack-decision",
            "agent_id": agent_id,
            "kind": "position",
            "content_md": position_md,
            "payload_json": payload,
        },
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("Starting bmg-harmony MCP server (stdio transport)")
    mcp.run(transport="stdio")
