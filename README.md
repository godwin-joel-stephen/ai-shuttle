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

## Evaluation

`python -m evals.run` (from `backend/`) runs the 24 cases in
`backend/evals/dataset.json` against the real agent, each in an isolated
`<database>_eval` database at a fixed moment, and scores task success (final
bookings), tool choice, cited sources and answer quality (an LLM judge that
also checks replies against the tool results). It reports latency, tokens,
estimated cost and fallback use.

```bash
python -m evals.run                                  # all cases
python -m evals.run --cases why-not-saturday         # selected cases
python -m evals.run --model gemini-3.1-flash-lite    # compare a model
python -m evals.run --save-baseline                  # record the baseline
python -m evals.run --check                          # fail on regression
```

A full run is about 100 Gemini requests; on the free tier that counts
against the same daily quota as the app.

## Tracing (self-hosted Langfuse)

Every assistant turn and eval case can be traced to a local Langfuse: model
calls with tokens and latency, each tool call with its input and result,
grouped by conversation, with eval scores attached. Everything stays on this
machine; telemetry is off.

```bash
python3 observability/setup_env.py     # secrets, project and keys (once)
docker compose -f observability/docker-compose.yml --env-file observability/.env up -d
open http://localhost:3000             # login printed by setup_env.py
```

Tracing is off unless `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are set
(setup_env.py adds them to `backend/.env`). Tests never trace.
