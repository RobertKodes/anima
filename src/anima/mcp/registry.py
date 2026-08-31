"""Registered MCP servers from config and experience packs."""

from __future__ import annotations

from anima.config.schema import AnimaConfig, McpServerConfig
from anima.mcp.client import McpToolInfo, call_tool_stdio, list_tools_stdio
from anima.mcp.sibyl_bridge import BUILTIN_SERVER_ID, SibylBridge


class McpRegistry:
    def __init__(self, cfg: AnimaConfig, memory=None) -> None:
        self.cfg = cfg
        self.memory = memory
        self.sibyl = SibylBridge(memory) if memory is not None else SibylBridge(_Disabled())
        self.servers: dict[str, McpServerConfig] = {
            s.id: s for s in cfg.mcp_servers if s.enabled
        }

    def list_servers(self) -> list[McpServerConfig]:
        return list(self.servers.values())

    def get(self, server_id: str) -> McpServerConfig:
        if server_id == BUILTIN_SERVER_ID:
            raise KeyError("built-in server — use discover_tools or call_builtin")
        if server_id not in self.servers:
            raise KeyError(server_id)
        return self.servers[server_id]

    def discover_tools(self, server_id: str) -> list[McpToolInfo]:
        if server_id == BUILTIN_SERVER_ID or server_id == "sibyl":
            return [
                McpToolInfo(server_id=BUILTIN_SERVER_ID, name=t.name, description=t.description)
                for t in self.sibyl.list_tools()
            ]
        server = self.get(server_id)
        return list_tools_stdio(server)

    def call(self, server_id: str, tool_name: str, arguments: dict | None = None) -> str:
        if server_id in {BUILTIN_SERVER_ID, "sibyl"}:
            return self.sibyl.call(tool_name, arguments)
        server = self.get(server_id)
        return call_tool_stdio(server, tool_name, arguments)

    def format_status(self) -> str:
        lines: list[str] = []
        if self.sibyl.available:
            tools = ", ".join(t.name for t in self.sibyl.list_tools())
            lines.append(f"Built-in {BUILTIN_SERVER_ID} (in-process Sibyl Memory): {tools}")
        else:
            lines.append(f"Built-in {BUILTIN_SERVER_ID}: off (amnesia or no store)")
        if not self.servers:
            if not lines:
                return (
                    "No external MCP servers configured.\n"
                    "Apply an experience pack or edit config.toml [[mcp_servers]]."
                )
            lines.append("\nNo external MCP servers configured.")
            lines.append("\nDiscover: /mcp tools anima-sibyl  ·  /mcp call anima-sibyl search {\"query\": \"Robert\"}")
            return "\n".join(lines)
        lines.append("\nExternal MCP servers:")
        for server in self.servers:
            opt = "optional" if server.optional else "required"
            lines.append(f"  • {server.id}  {server.command} {' '.join(server.args)}  ({opt})")
        lines.append("\nDiscover: /mcp tools <server_id>  ·  Call: /mcp call <server> <tool> [json]")
        return "\n".join(lines)


class _Disabled:
    enabled = False
