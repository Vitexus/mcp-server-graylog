import argparse

from . import __version__
from .server import main as run


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mcp-server-graylog",
        description="stdio MCP bridge to Graylog's built-in /api/mcp endpoint. "
        "Env: GRAYLOG_URL, GRAYLOG_API_TOKEN, GRAYLOG_READ_ONLY (default true), "
        "GRAYLOG_TIMEOUT, GRAYLOG_VERIFY_TLS, GRAYLOG_MAX_CHARS.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.parse_args()
    run()


if __name__ == "__main__":
    main()
