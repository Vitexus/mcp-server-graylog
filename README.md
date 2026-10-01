# mcp-server-graylog

stdio MCP bridge to the MCP endpoint built into **Graylog 7.1+** (`/api/mcp`).
Graylog marks its MCP support as **experimental**: use a dedicated read-only Graylog user, and do not point one client at several Graylog instances.

## Install

    apt install mcp-server-graylog            # server
    apt install mcprack-mcp-server-graylog    # optional: register in mcprack

## Graylog setup
1. Create a read-only user and an API token (System > Users and Teams > Tokens).
2. Enable *System > Configurations > MCP*.

## Environment

| Variable | Secret | Default | Meaning |
|---|---|---|---|
| `GRAYLOG_API_TOKEN` | yes | – | raw API token (the bridge builds `Basic base64("<token>:token")` itself) |
| `GRAYLOG_URL` | no | `http://127.0.0.1:9000` | Graylog base URL |
| `GRAYLOG_READ_ONLY` | no | `true` | expose only tools with `readOnlyHint=true` (fails closed if a hint is missing) |
| `GRAYLOG_TIMEOUT` | no | `30` | seconds per request |
| `GRAYLOG_VERIFY_TLS` | no | `true` | verify the server certificate |
| `GRAYLOG_MAX_CHARS` | no | `100000` | truncate larger tool output |

## Tools
Discovered from Graylog at runtime (names are never changed). Upstream annotations are kept; missing hints are filled from the tool name (`get_/list_/search_…` = read-only, `create_/add_/send_…` = create, anything else = destructive).

## Development

    PYTHONPATH=src python3 -m pytest
