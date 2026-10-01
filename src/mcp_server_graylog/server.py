"""Bridge: serve Graylog's remote MCP tools over stdio."""

import asyncio
import logging
import sys
from typing import Any

from fastmcp.client import Client, StreamableHttpTransport
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp_types import (
    CallToolRequestParams,
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)

from . import __version__
from .annotations import complete, title_from_name
from .config import Config

logger = logging.getLogger(__name__)


def _error(message: str) -> CallToolResult:
    return CallToolResult(content=[TextContent(type="text", text=message)], is_error=True)


def _truncate(result: CallToolResult, limit: int) -> CallToolResult:
    used = 0
    for block in result.content:
        text = getattr(block, "text", None)
        if text is None:
            continue
        room = max(limit - used, 0)
        if len(text) > room:
            block.text = text[:room] + f"\n[truncated: output exceeded {limit} characters]"
        used += len(text)
    return result


class Bridge:
    def __init__(self, config: Config, client: Client | None = None) -> None:
        self.config = config
        self._client = client

    def _make_client(self) -> Client:
        if self._client is not None:
            return self._client
        transport = StreamableHttpTransport(
            self.config.endpoint,
            headers={"Authorization": self.config.auth_header()},
            verify=self.config.verify_tls,
        )
        return Client(transport, timeout=self.config.timeout)

    async def list_tools(self) -> list[Tool]:
        async with self._make_client() as client:
            upstream = await client.list_tools_mcp()
        tools = []
        for tool in upstream.tools:
            ann = complete(tool.name, tool.annotations)
            if self.config.read_only and not ann.read_only_hint:
                continue
            tools.append(
                tool.model_copy(update={"title": tool.title or ann.title or title_from_name(tool.name), "annotations": ann})
            )
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> CallToolResult:
        try:
            visible = {t.name for t in await self.list_tools()}
            if name not in visible:
                return _error(f"Tool '{name}' is not available (read-only mode or unknown tool).")
            async with self._make_client() as client:
                result = await client.call_tool_mcp(name, arguments, timeout=self.config.timeout)
            return _truncate(result, self.config.max_chars)
        except RuntimeError as exc:
            return _error(str(exc))
        except Exception as exc:  # never leak headers/tokens or stack traces
            logger.error("Graylog MCP call failed: %s", type(exc).__name__)
            return _error(f"Graylog MCP request failed ({type(exc).__name__}). Check GRAYLOG_URL, the token and that MCP is enabled in Graylog.")


def build_server(bridge: Bridge) -> Server:
    async def on_list_tools(context, params) -> ListToolsResult:
        try:
            return ListToolsResult(tools=await bridge.list_tools())
        except Exception as exc:
            logger.error("Cannot list Graylog tools: %s", type(exc).__name__)
            return ListToolsResult(tools=[])

    async def on_call_tool(context, params: CallToolRequestParams) -> CallToolResult:
        return await bridge.call_tool(params.name, params.arguments or {})

    return Server(
        "mcp-server-graylog",
        version=__version__,
        description="stdio bridge to the Graylog built-in MCP endpoint",
        on_list_tools=on_list_tools,
        on_call_tool=on_call_tool,
    )


async def run_server() -> None:
    config = Config.from_env()
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    logger.info("Graylog endpoint: %s (read-only: %s)", config.endpoint, config.read_only)
    app = build_server(Bridge(config))
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-server-graylog",
                server_version=__version__,
                capabilities=app.get_capabilities(notification_options=NotificationOptions(), experimental_capabilities={}),
            ),
        )


def main() -> None:
    asyncio.run(run_server())
