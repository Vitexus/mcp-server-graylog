"""stdio bridge to Graylog's built-in MCP endpoint."""

try:
    from importlib.metadata import version

    __version__ = version("mcp-server-graylog")
except Exception:  # pragma: no cover
    __version__ = "0.0.0+unknown"
