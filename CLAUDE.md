# Clear Path (AI Shuttle POC)

An iOS commuter-shuttle app whose AI works through the OS (Siri, widgets,
Control Center, Live Activities, notifications, share sheet) rather than a
chatbot, backed by a FastAPI + LangGraph agent with RAG, MCP (both
directions), evaluation and tracing. It is a portfolio demo of production
mobile + AI engineering. Demo days: Tuesday or Thursday.

Read these before working on an area:

| Doc | Covers |
|---|---|
| [docs/PRODUCT.md](docs/PRODUCT.md) | Goal, flows F1–F13 and their status, design principles |
| [docs/PROGRESS.md](docs/PROGRESS.md) | What's done, what's next, known issues, decision log |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System diagram, layers, how each surface reaches the backend |
| [docs/BACKEND.md](docs/BACKEND.md) | FastAPI app, endpoints, booking rules, data model, scripts, tests |
| [docs/AI.md](docs/AI.md) | Agent graph, tools, prompt, models and fallbacks, RAG, evaluation, Langfuse |
| [docs/MOBILE.md](docs/MOBILE.md) | iOS targets, Siri intents, widgets, Live Activity, trip mode, voice, tests |
| [docs/MCP.md](docs/MCP.md) | MCP server (Claude Desktop), MCP client, weather server |
| [docs/DEMO_RUNBOOK.md](docs/DEMO_RUNBOOK.md) | Exact setup commands and the demo script |

## Repository map

```
AIShuttle/                 Xcode project (iOS 26.4, Swift, SwiftUI)
  AIShuttle/               app target: AppIntent/, Assistant/, Tracking/, Views/, ViewModels/
  ClearPathWidgets/        widget extension: widget, control, Live Activity UI
  ClearPathShare/          share extension: schedule import in the share sheet
  ScheduleImport/          schedule import pipeline (app + share extension): OCR, on-device model, review UI
  ScheduleImportEvals/     macOS eval + demo sample generator for schedule extraction (run.sh)
  Shared/                  compiled into both targets: API client, DTOs, one-tap intent
  AIShuttleTests/          Swift Testing unit tests
backend/                   Python 3.14, FastAPI, LangGraph, SQLAlchemy, Postgres+pgvector
  app/                     api/ agent/ graph/ tools/ services/ repositories/ models/ rag/ ...
  evals/                   evaluation harness, dataset, baseline
  knowledge/               policy documents for RAG
  mcp_servers/weather.py   standalone weather MCP server
  scripts/                 demo_trip, reset/rebuild DB, ingest knowledge
  tests/                   pytest suite (isolated _test database)
observability/             self-hosted Langfuse (docker compose + setup_env.py)
docker-compose.yml         app Postgres (pgvector/pgvector:pg17-trixie)
```

## Run it

```bash
# Postgres (and Langfuse, if started once) run in Docker Desktop
docker compose up -d
cd backend && source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000      # backend for the iPhone
python -m pytest -q                                 # 143 tests, ~6s, no network
python -m scripts.demo_trip                         # live simulated trip for demos
```

iOS: open `AIShuttle/AIShuttle.xcodeproj`, scheme **AIShuttle**, run on
"Godwin's iPhone". The backend address is the `BOOKING_API_BASE_URL` build
setting (currently `http://192.168.1.6:8000`; check with
`ipconfig getifaddr en0` and update if the Mac's IP changes).

## Working agreements (from the user)

- **Never use anything that costs money without discussing it first.**
  Gemini runs on the free tier; Langfuse is self-hosted; no paid APIs,
  hosting or developer accounts. Ration free quota (see AI.md).
- Work in feature branches; commit with clear messages; merge to `main` and
  push only when the user says so (they usually ask at the end of a phase).
- Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- The user tests on a real iPhone (iOS 27.0.1) and reports back; give
  step-by-step test instructions after each change, and ask for logs and
  screenshots when something fails.
- No CI (the user declined it).
- Single user: user id 1 ("Godwin Joel"). There is no child/Emma model.

## Pitfalls that already cost time

- **Xcode 26.4.1 build hang**: builds stall on "Discovering version info for
  clang" (the build service stops reading `clang -v -E -dM`). Fix:
  `pkill -f "clang -v -E -dM"`. Command-line builds from the agent hang the
  same way; run xcodebuild through a loop that kills that probe after ~5s.
- **Isolated databases**: tests and evals call
  `app.isolated_database.use_isolated_database()` *before* importing
  anything from `app.db` (importing `app.db` connects with the original
  URL). Both assert they're on `_test` / `_eval`. Never move that helper
  into `app.db`.
- **zsh**: don't name a shell variable `path` (it's tied to `PATH`).
- **Free-tier Gemini**: `gemini-3.5-flash` allows 20 requests/day; a full
  eval run is ~100 requests; per-minute limits cause 429s/timeouts.
- **Siri on iOS 27** routes with its own model: exact App Shortcut phrases
  still miss sometimes; "Where's my shuttle…" spoken is often answered by
  Siri itself — use "Track my shuttle with Clear Path".
- **Swift concurrency**: the app target defaults to MainActor isolation;
  UNUserNotificationCenter delegate callbacks must complete on the main
  thread (use completion-handler variants), or SwiftUI asserts.
