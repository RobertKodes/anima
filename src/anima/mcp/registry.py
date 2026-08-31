"""Registered MCP servers from config and experience packs."""

from __future__ import annotations

from anima.config.schema import AnimaConfig, McpServerConfig
from anima.mcp.client import McpToolInfo, call_tool_stdio, list_tools_stdio


class McpRegistry:
    def __init__(self, cfg: AnimaConfig) -> None:
        self.cfg = cfg
        self.servers: dict[str, McpServerConfig] = {
            s.id: s for s in cfg.mcp_servers if s.enabled
        }

    def list_servers(self) -> list[McpServerConfig]:
        return list(self.servers.values())

    def get(self, server_id: str) -> McpServerConfig:
        if server_id not in self.servers:
            raise KeyError(server_id)
        return self.servers[server_id]

    def discover_tools(self, server_id: str) -> list[McpToolInfo]:
        server = self.get(server_id)
        return list_tools_stdio(server)

    def call(self, server_id: str, tool_name: str, arguments: dict | None = None) -> str:
        server = self.get(server_id)
        return call_tool_stdio(server, tool_name, arguments)

    def format_status(self) -> str:
        if not self.servers:
            return (
                "No MCP servers configured.\n"
                "Apply an experience pack (anima experiences apply scholar) or edit config.toml [[mcp_servers]]."
            )
        lines = ["MCP servers:"]
        for server in self.servers:
            opt = "optional" if server.optional else "required"
            lines.append(f"  • {server.id}  {server.command} {' '.join(server.args)}  ({opt})")
        lines.append("\nDiscover: /mcp tools <server_id>  ·  Call: /mcp call <server> <tool> [json]")
        return "\n".join(lines)
