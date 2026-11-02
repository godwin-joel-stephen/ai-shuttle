# ai-shuttle
A scalable AI-powered shuttle platform demonstrating Agentic AI, Siri integration, MCP, intelligent booking workflows, and AI evaluation.

## MCP server

Clear Path's agent tools (bookings, shuttle options, live status, booking
rules and policy search) are also available over the Model Context Protocol,
so any MCP client can use them. Calls go through the same services and
booking rules as the app.

Run it over stdio (desktop clients) or Streamable HTTP:

```bash
cd backend && source .venv/bin/activate
python -m app.mcp_server                # stdio
python -m app.mcp_server --http 8001    # http://localhost:8001/mcp
```

**Claude Code:**

```bash
claude mcp add clear-path --env PYTHONPATH=/path/to/ai-shuttle/backend -- \
  /path/to/ai-shuttle/backend/.venv/bin/python -m app.mcp_server
```

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "clear-path": {
      "command": "/path/to/ai-shuttle/backend/.venv/bin/python",
      "args": ["-m", "app.mcp_server"],
      "env": { "PYTHONPATH": "/path/to/ai-shuttle/backend" }
    }
  }
}
```

Postgres must be running (`docker compose up -d`). The server acts for user 1;
set `CLEAR_PATH_USER_ID` to change that.
