# MCP (Model Context Protocol)

MCP Python SDK **2.3.0** (2.x renamed `FastMCP` to
`mcp.server.mcpserver.MCPServer`; `langchain-mcp-adapters` 0.3.1 is not
compatible with 2.x, so the client adapter is our own).

## Clear Path as an MCP server (`backend/app/mcp_server.py`)

- Publishes the in-app agent's tools (wrapping the same LangChain tools, so
  the same services and booking rules) plus `get_today`: 9 tools.
- Each call opens a fresh DB session and builds the tools for user 1
  (`CLEAR_PATH_USER_ID` to change). Input schemas come from the tool
  functions' signatures.
- Annotations: read-only vs mutating; `cancel_booking` destructive.
- Transports: `python -m app.mcp_server` (stdio, desktop clients) and
  `--http 8001` (Streamable HTTP at `/mcp`).
- Verified in **Claude Desktop** (2026-11-04): list bookings, book Friday
  (appears in the iPhone app), Saturday refused by the backend rule, policy
  answer.

Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`,
add next to the existing `"preferences"` key):

```json
"mcpServers": {
  "clear-path": {
    "command": "/Users/godwinjoel.j/Projects/ai-shuttle/backend/.venv/bin/python",
    "args": ["-m", "app.mcp_server"],
    "env": { "PYTHONPATH": "/Users/godwinjoel.j/Projects/ai-shuttle/backend" }
  }
}
```

Needs Docker (Postgres) running. Claude Code: `claude mcp add clear-path
--env PYTHONPATH=<backend> -- <backend>/.venv/bin/python -m app.mcp_server`.

## The agent as an MCP client (`backend/app/agent/mcp_tools.py`)

- `ExternalMCPTools` launches each server in `settings.mcp_servers` over
  stdio at backend startup (lifespan), lists tools, and wraps them as
  LangChain `StructuredTool`s (JSON-schema args, `metadata={"mcp_server": name}`).
- Sessions live on a dedicated event-loop thread; each server's session is
  opened and closed inside one task (stdio transport requirement); sync
  tool calls are submitted to that loop (10s timeout).
- A server that fails to start is skipped with a warning.
- `errlog=sys.__stderr__` (a replaced `sys.stderr`, e.g. under pytest, has no fd).

## Weather MCP server (`backend/mcp_servers/weather.py`)

Standalone (imports nothing from `app`), Open-Meteo (free, no key):
`get_current_weather(latitude, longitude)` → conditions, temperature,
precipitation, wind, rain chance next 2h. The agent calls it with the pickup
stop's coordinates for "Should I leave now?".

## Demo

1. Claude Desktop: "Book my usual shuttle for Wednesday" → permission →
   booked → refresh the iPhone app.
2. "Book Saturday too" → refused by the backend rule.
3. Phone: Ask Clear Path → "Should I leave now?" → action row
   "Checked the weather · via weather MCP server".
Line: *"MCP both ways: Clear Path is a tool for any AI, and its agent can use any tool."*
