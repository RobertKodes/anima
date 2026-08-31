"""MCP client — optional; requires pip install anima[mcp]."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

from anima.config.schema import McpServerConfig


@dataclass
class McpToolInfo:
    server_id: str
    name: str
    description: str = ""


def list_tools_stdio(server: McpServerConfig) -> list[McpToolInfo]:
    """Discover tools from an MCP server via stdio. Returns [] if mcp SDK missing."""
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError:
        return []

    async def _run() -> list[McpToolInfo]:
        params = StdioServerParameters(command=server.command, args=server.args, env=server.env or None)
        tools: list[McpToolInfo] = []
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                for tool in result.tools:
                    tools.append(
                        McpToolInfo(server_id=server.id, name=tool.name, description=tool.description or "")
                    )
        return tools

    try:
        return asyncio.run(_run())
    except Exception:
        return []


def call_tool_stdio(server: McpServerConfig, tool_name: str, arguments: dict[str, Any] | None = None) -> str:
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError:
        return "MCP SDK not installed. Run: pip install 'anima[mcp]'"

    async def _run() -> str:
        params = StdioServerParameters(command=server.command, args=server.args, env=server.env or None)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments or {})
                parts = []
                for block in result.content:
                    text = getattr(block, "text", None)
                    if text:
                        parts.append(text)
                    else:
                        parts.append(str(block))
                return "\n".join(parts) or json.dumps({"ok": True})

    try:
        return asyncio.run(_run())
    except Exception as exc:
        return f"MCP call failed: {exc}"
