import base64

import pytest
from fastmcp import FastMCP
from fastmcp.client import Client
from mcp_types import ToolAnnotations

from mcp_server_graylog.config import Config
from mcp_server_graylog.server import Bridge


def _upstream() -> FastMCP:
    mcp = FastMCP("fake-graylog")

    @mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
    def list_streams() -> str:
        return "x" * 50

    @mcp.tool()
    def create_widget(name: str) -> str:
        return f"created {name}"

    @mcp.tool()
    def delete_stream(stream_id: str) -> str:
        return "deleted"

    return mcp


def _bridge(read_only: bool, max_chars: int = 1000) -> Bridge:
    cfg = Config(token="SECRET", read_only=read_only, max_chars=max_chars)
    return Bridge(cfg, client=Client(_upstream()))


def test_auth_header():
    expected = "Basic " + base64.b64encode(b"tok:token").decode()
    assert Config(token="tok").auth_header() == expected


def test_missing_token_raises():
    with pytest.raises(RuntimeError):
        Config().auth_header()


async def test_all_tools_have_title_and_full_hints():
    tools = await _bridge(read_only=False).list_tools()
    assert {t.name for t in tools} == {"list_streams", "create_widget", "delete_stream"}
    for t in tools:
        assert t.title and t.title != t.name
        a = t.annotations
        assert None not in (a.read_only_hint, a.destructive_hint, a.idempotent_hint, a.open_world_hint)
        assert not (a.read_only_hint and a.destructive_hint)


async def test_name_consistency():
    by_name = {t.name: t for t in await _bridge(read_only=False).list_tools()}
    assert by_name["list_streams"].annotations.read_only_hint is True
    assert by_name["delete_stream"].annotations.destructive_hint is True


async def test_read_only_hides_mutating_tools():
    tools = await _bridge(read_only=True).list_tools()
    assert [t.name for t in tools] == ["list_streams"]


async def test_read_only_blocks_call():
    res = await _bridge(read_only=True).call_tool("delete_stream", {"stream_id": "1"})
    assert res.is_error


async def test_call_passthrough_and_truncate():
    res = await _bridge(read_only=True, max_chars=10).call_tool("list_streams", {})
    assert not res.is_error
    assert "truncated" in res.content[0].text


async def test_error_does_not_leak_secret():
    class Boom:
        async def __aenter__(self):
            raise ConnectionError("Authorization: Basic SECRET")

        async def __aexit__(self, *a):
            return False

    bridge = Bridge(Config(token="SECRET"), client=Boom())
    res = await bridge.call_tool("list_streams", {})
    assert res.is_error and "SECRET" not in res.content[0].text
