"""Phase 2 FastMCP smoke tests."""

import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _tool_text(result) -> dict:
    return json.loads(result.content[0].text)


def test_phase2_tools_over_stdio(tmp_path):
    asyncio.run(_phase2_tools_over_stdio(tmp_path))


async def _phase2_tools_over_stdio(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    db_path = tmp_path / "harmony.sqlite"
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(project_root / "server" / "harmony_server.py")],
        env={
            **os.environ,
            "HARMONY_DB_PATH": str(db_path),
            "PYTHONPATH": str(project_root),
        },
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            tool_names = {tool.name for tool in tools.tools}
            assert {
                "ack_message",
                "reply_message",
                "get_battle_card",
                "append_proving_envelope",
            }.issubset(tool_names)

            post = await session.call_tool(
                "post_message",
                arguments={
                    "thread_id": "phase2-mcp",
                    "agent_id": "codex",
                    "kind": "message",
                    "content_md": "MCP smoke root",
                },
            )
            event_id = _tool_text(post)["event_id"]

            ack = await session.call_tool(
                "ack_message",
                arguments={"message_id": event_id, "agent_id": "claude"},
            )
            assert _tool_text(ack)["validation_status"] == "ok"

            envelope = await session.call_tool(
                "append_proving_envelope",
                arguments={
                    "thread_id": "phase2-mcp",
                    "agent_id": "codex",
                    "proved": "- MCP tool list\n- MCP write path",
                    "not_checked": "- Live dogfood store",
                    "confidence": 0.8,
                },
            )
            assert _tool_text(envelope)["validation_status"] == "ok"

            card = await session.call_tool(
                "get_battle_card",
                arguments={"thread_id": "phase2-mcp"},
            )
            card_data = _tool_text(card)
            assert card_data["thread_id"] == "phase2-mcp"
            assert card_data["envelope_count"] == 1
            assert card_data["unacked_count"] == 0
