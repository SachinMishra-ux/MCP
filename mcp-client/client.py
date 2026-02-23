"""
client.py — Custom MCP Multi-Server Client

Manages connections to multiple MCP servers defined in config.yaml.
Supports both stdio (local process) and HTTP transports.
"""

import asyncio
import json
import os
import yaml
from pathlib import Path
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.types import Tool

# ─────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────

@dataclass
class ServerConfig:
    name: str
    type: str           # "stdio" or "http"
    description: str = ""
    enabled: bool = True
    # stdio-specific
    command: List[str] = field(default_factory=list)
    cwd: Optional[str] = None
    # http-specific
    url: Optional[str] = None
    auth_token: Optional[str] = None


@dataclass
class ConnectedServer:
    name: str
    session: ClientSession
    tools: List[Tool] = field(default_factory=list)


@dataclass
class ToolCallResult:
    server: str
    tool: str
    arguments: Dict[str, Any]
    result: Any
    is_error: bool = False
    error_message: str = ""


# ─────────────────────────────────────────────────────────────
# Config loader
# ─────────────────────────────────────────────────────────────

CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_server_configs(config_path: Path = CONFIG_PATH) -> Dict[str, ServerConfig]:
    """Load server definitions from config.yaml."""
    with open(config_path, "r") as f:
        raw = yaml.safe_load(f)

    servers: Dict[str, ServerConfig] = {}
    for name, cfg in raw.get("servers", {}).items():
        servers[name] = ServerConfig(
            name=name,
            type=cfg.get("type", "stdio"),
            description=cfg.get("description", ""),
            enabled=cfg.get("enabled", True),
            command=cfg.get("command", []),
            cwd=cfg.get("cwd"),
            url=cfg.get("url"),
            auth_token=cfg.get("auth_token"),
        )
    return servers


def save_server_configs(servers: Dict[str, ServerConfig], config_path: Path = CONFIG_PATH):
    """Persist server configs back to config.yaml."""
    data: Dict = {"servers": {}}
    for name, cfg in servers.items():
        entry: Dict[str, Any] = {
            "type": cfg.type,
            "description": cfg.description,
            "enabled": cfg.enabled,
        }
        if cfg.type == "stdio":
            entry["command"] = cfg.command
            if cfg.cwd:
                entry["cwd"] = cfg.cwd
        else:
            entry["url"] = cfg.url
            if cfg.auth_token:
                entry["auth_token"] = cfg.auth_token
        data["servers"][name] = entry

    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def add_remote_server(
    name: str,
    url: str,
    auth_token: Optional[str] = None,
    description: str = "",
    config_path: Path = CONFIG_PATH,
) -> Dict[str, ServerConfig]:
    """Add a new HTTP server to the config and return updated configs."""
    servers = load_server_configs(config_path)
    servers[name] = ServerConfig(
        name=name,
        type="http",
        url=url,
        auth_token=auth_token,
        description=description or f"Remote server at {url}",
        enabled=True,
    )
    save_server_configs(servers, config_path)
    return servers


# ─────────────────────────────────────────────────────────────
# MCPMultiClient
# ─────────────────────────────────────────────────────────────

class MCPMultiClient:
    """
    Manages multiple MCP server connections.

    Usage (as async context manager):
        async with MCPMultiClient() as client:
            await client.connect("filesystem")
            tools = client.get_all_tools()
            result = await client.call_tool("filesystem", "list_directory", {"path": "/tmp"})
    """

    def __init__(self, config_path: Path = CONFIG_PATH):
        self.config_path = config_path
        self.server_configs: Dict[str, ServerConfig] = {}
        self.connected: Dict[str, ConnectedServer] = {}
        # Keep track of background task handles & exit stacks per server
        self._exit_stacks: Dict[str, Any] = {}
        self._tasks: Dict[str, asyncio.Task] = {}

    # ── Lifecycle ────────────────────────────────────────────

    async def __aenter__(self):
        self.server_configs = load_server_configs(self.config_path)
        return self

    async def __aexit__(self, *_):
        await self.disconnect_all()

    def reload_config(self):
        """Reload config from disk (e.g., after adding a server via the UI)."""
        self.server_configs = load_server_configs(self.config_path)

    # ── Connection management ─────────────────────────────────

    async def connect(self, server_name: str) -> Tuple[bool, str]:
        """
        Connect to a server by name.
        Returns (success: bool, message: str).
        """
        if server_name in self.connected:
            return True, f"Already connected to '{server_name}'."

        cfg = self.server_configs.get(server_name)
        if not cfg:
            return False, f"Server '{server_name}' not found in config."

        try:
            if cfg.type == "stdio":
                return await self._connect_stdio(server_name, cfg)
            elif cfg.type == "http":
                return await self._connect_http(server_name, cfg)
            else:
                return False, f"Unknown transport type: {cfg.type}"
        except Exception as e:
            return False, f"Connection error: {e}"

    async def _connect_stdio(self, name: str, cfg: ServerConfig) -> Tuple[bool, str]:
        """Spawn a subprocess and connect via stdio."""
        # Resolve cwd relative to config file directory
        cwd = None
        if cfg.cwd:
            base = self.config_path.parent
            cwd = str((base / cfg.cwd).resolve())

        params = StdioServerParameters(
            command=cfg.command[0],
            args=cfg.command[1:],
            env=None,
            cwd=cwd,
        )

        import contextlib
        stack = contextlib.AsyncExitStack()
        await stack.__aenter__()

        try:
            read, write = await stack.enter_async_context(stdio_client(params))
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            tools_response = await session.list_tools()
            tools = tools_response.tools

            self.connected[name] = ConnectedServer(name=name, session=session, tools=tools)
            self._exit_stacks[name] = stack
            return True, f"Connected to '{name}' via stdio. {len(tools)} tool(s) available."
        except Exception as e:
            await stack.__aexit__(type(e), e, e.__traceback__)
            return False, f"stdio connection failed: {e}"

    async def _connect_http(self, name: str, cfg: ServerConfig) -> Tuple[bool, str]:
        """Connect to a running HTTP MCP server."""
        import contextlib
        import httpx
        stack = contextlib.AsyncExitStack()
        await stack.__aenter__()

        try:
            headers = {}
            if cfg.auth_token:
                headers["Authorization"] = f"Bearer {cfg.auth_token}"
            
            http_client = httpx.AsyncClient(headers=headers, timeout=30.0)

            read, write, *_ = await stack.enter_async_context(
                streamable_http_client(cfg.url, http_client=http_client)
            )
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            tools_response = await session.list_tools()
            tools = tools_response.tools

            self.connected[name] = ConnectedServer(name=name, session=session, tools=tools)
            self._exit_stacks[name] = stack
            return True, f"Connected to '{name}' via HTTP ({cfg.url}). {len(tools)} tool(s) available."
        except Exception as e:
            await stack.__aexit__(type(e), e, e.__traceback__)
            return False, f"HTTP connection failed: {e}"

    async def disconnect(self, server_name: str) -> Tuple[bool, str]:
        """Disconnect a named server."""
        if server_name not in self.connected:
            return False, f"'{server_name}' is not connected."
        stack = self._exit_stacks.pop(server_name, None)
        if stack:
            try:
                await stack.__aexit__(None, None, None)
            except Exception:
                pass
        self.connected.pop(server_name, None)
        return True, f"Disconnected from '{server_name}'."

    async def disconnect_all(self):
        """Disconnect all servers cleanly."""
        for name in list(self.connected.keys()):
            await self.disconnect(name)

    # ── Tool access ───────────────────────────────────────────

    def get_all_tools(self) -> List[Dict]:
        """
        Return a flat list of all tools across connected servers.
        Each entry: {"server": str, "tool": Tool}
        """
        result = []
        for srv_name, srv in self.connected.items():
            for tool in srv.tools:
                result.append({"server": srv_name, "tool": tool})
        return result

    def get_tools_for_llm(self) -> List[Dict]:
        """
        Return tools in Anthropic-compatible format, namespaced as
        "{server}__{tool_name}" to avoid name collisions across servers.
        Server names are sanitized to only include alphanumeric characters,
        hyphens, and underscores to satisfy OpenAI strict naming (^[a-zA-Z0-9_-]+$).
        """
        tools_for_llm = []
        for entry in self.get_all_tools():
            tool: Tool = entry["tool"]
            server: str = entry["server"]
            
            # Sanitize server name for OpenAI strict regex ^[a-zA-Z0-9_-]+$
            safe_server = self._sanitize_name(server)

            # Build Anthropic-style tool schema
            tools_for_llm.append({
                "name": f"{safe_server}__{tool.name}",
                "description": (
                    f"[{server}] {tool.description or tool.name}"
                ),
                "input_schema": tool.inputSchema or {"type": "object", "properties": {}},
            })
        return tools_for_llm

    def find_server_for_tool(self, namespaced_tool_name: str) -> Optional[Tuple[str, str]]:
        """
        Given a namespaced tool name like "filesystem__list_directory",
        returns (server_name, tool_name) or None if not found.
        """
        if "__" in namespaced_tool_name:
            parts = namespaced_tool_name.split("__", 1)
            server_name, tool_name = parts[0], parts[1]
            if server_name in self.connected:
                return server_name, tool_name

        # Fallback: search all servers by raw tool name
        for srv_name, srv in self.connected.items():
            for tool in srv.tools:
                if tool.name == namespaced_tool_name:
                    return srv_name, tool.name
        return None

    def _sanitize_name(self, name: str) -> str:
        """Sanitize name to satisfy OpenAI tool naming regex: ^[a-zA-Z0-9_-]+$"""
        import re
        return re.sub(r'[^a-zA-Z0-9_-]', '_', name)

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool on a specific server and return structured result."""
        # Try direct lookup first
        srv = self.connected.get(server_name)
        
        # If not found, it might be a sanitized name from the LLM
        if not srv:
            for actual_name in self.connected:
                if self._sanitize_name(actual_name) == server_name:
                    server_name = actual_name
                    srv = self.connected[server_name]
                    break

        if not srv:
            return ToolCallResult(
                server=server_name,
                tool=tool_name,
                arguments=arguments,
                result=None,
                is_error=True,
                error_message=f"Server '{server_name}' is not connected.",
            )
        try:
            response = await srv.session.call_tool(tool_name, arguments)
            # Extract text content
            content = response.content
            if content and hasattr(content[0], "text"):
                result_text = content[0].text
            else:
                result_text = json.dumps([c.model_dump() for c in content], indent=2)

            return ToolCallResult(
                server=server_name,
                tool=tool_name,
                arguments=arguments,
                result=result_text,
                is_error=response.isError or False,
                error_message=result_text if response.isError else ""
            )
        except Exception as e:
            return ToolCallResult(
                server=server_name,
                tool=tool_name,
                arguments=arguments,
                result=None,
                is_error=True,
                error_message=f"{type(e).__name__}: {str(e)}",
            )

    # ── Convenience ───────────────────────────────────────────

    def list_server_status(self) -> List[Dict]:
        """Return status of all configured servers."""
        status = []
        for name, cfg in self.server_configs.items():
            status.append({
                "name": name,
                "description": cfg.description,
                "type": cfg.type,
                "url": cfg.url if cfg.type == "http" else (cfg.cwd or ""),
                "enabled": cfg.enabled,
                "connected": name in self.connected,
                "tool_count": len(self.connected[name].tools) if name in self.connected else 0,
            })
        return status
