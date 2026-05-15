from __future__ import annotations

import json
import os
from pathlib import Path
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools


CONFIG_PATH = Path(__file__).parent.parent / "mcp_config.json"


def _resolve_env(env_dict: dict[str, str] | None) -> dict[str, str]:
    if not env_dict:
        return {}
    resolved = {}
    for k, v in env_dict.items():
        if v.startswith("${") and v.endswith("}"):
            env_key = v[2:-1]
            resolved[k] = os.getenv(env_key, "")
        else:
            resolved[k] = v
    return resolved


def load_mcp_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


async def create_mcp_tools(exit_stack: AsyncExitStack) -> list:
    config = load_mcp_config()
    all_tools = []

    for server_name, server_cfg in config["mcpServers"].items():
        print(f"[MCP] Spawning server: {server_name}", flush=True)
        env = _resolve_env(server_cfg.get("env"))
        full_env = {**os.environ, **env}

        params = StdioServerParameters(
            command=server_cfg["command"],
            args=server_cfg.get("args", []),
            env=full_env,
        )

        try:
            stdio_transport = await exit_stack.enter_async_context(
                stdio_client(params)
            )
            read_stream, write_stream = stdio_transport
            session = await exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await session.initialize()
            print(f"[MCP] {server_name} initialized", flush=True)

            tools = await load_mcp_tools(session)
            print(f"[MCP] {server_name} loaded {len(tools)} tools: {[t.name for t in tools]}", flush=True)
            all_tools.extend(tools)
        except Exception as e:
            print(f"[MCP] ERROR spawning {server_name}: {e}", flush=True)

    print(f"[MCP] Total tools loaded: {len(all_tools)}", flush=True)
    return all_tools
