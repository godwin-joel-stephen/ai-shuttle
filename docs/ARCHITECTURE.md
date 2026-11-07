# Architecture

## Overview

```
 iPhone (iOS 26.4+, tested on iOS 27)                         Mac (dev machine, same Wi-Fi)
 ┌────────────────────────────────────────┐                   ┌──────────────────────────────────────────┐
 │ Siri / App Shortcuts (App Intents)     │                   │ FastAPI  (uvicorn :8000)                 │
 │   Book, Track, Ask Clear Path, snippet │──HTTP JSON──┐     │   /bookings  (structured, no LLM)        │
 │ Widgets / Control / Action button      │             │     │   /assistant (LangGraph tool agent)      │
 │ Live Activity (Lock Screen, Island)    │             ├────▶│   /tracking, /simulator, /users/location │
 │ Trip mode (background location,        │             │     │   /schedule  (typed days, no LLM)        │
 │   local notifications, Rebook action)  │             │     │ Agent ─▶ Tools ─▶ Services ─▶ Repos ─▶ PG │
 │ App: home, rides, map, chat + voice    │─────────────┤     │   │        │                             │
 │ Share sheet / Import work schedule:    │             │     │   │        │                             │
 │   Vision OCR + Foundation Models       │─typed days──┘     │   │        │                             │
 │   (on-device; text never leaves)       │                   │   │        │                             │
 └────────────────────────────────────────┘                   │   │        ├─ RAG: pgvector + fastembed  │
                                                              │   │        └─ external MCP tools (weather)│
 Claude Desktop / any MCP client ──stdio──▶ app.mcp_server ───│───┘ (same tools, same rules)             │
                                                              │ Gemini (free tier) via langchain-google-genai
                                                              │ Langfuse (self-hosted, Docker) ◀─ traces  │
                                                              └──────────────────────────────────────────┘
```

Docker containers on the Mac:
- `ai-shuttle-postgres` (pgvector/pgvector:pg17-trixie) on 5432: app data,
  policy embeddings, LangGraph conversation checkpoints, plus `_test` and
  `_eval` databases.
- `langfuse-*` (web :3000, worker, postgres, clickhouse, redis, minio) from
  `observability/docker-compose.yml`; only the UI and MinIO listen on
  localhost.

## Backend layering

```
API (FastAPI routers)  →  Agent/Graph (LangGraph)  →  Tools (LangChain)  →  Services  →  Repositories  →  PostgreSQL
```

- The LLM is only in the agent layer; it never touches the database.
- Services hold every business rule (service days, booking window,
  cut-off, seats, idempotent booking, moves, cancellations, tracking).
- The same tools serve the in-app agent, the MCP server and the evals.
- `app.core.clock` is the single source of "now" (tests and evals pin it).

## How each surface reaches the backend

| Surface | Path | LLM? |
|---|---|---|
| Siri "Book my usual shuttle…" (`BookMyUsualShuttleIntent`) | `POST /bookings {booking_date}` → booking graph skips understanding | No |
| Siri card Earlier/Later (`RescheduleBookingIntent`) | `POST /bookings/{id}/reschedule` | No |
| Widget button / Control / Action button (`BookTomorrowIntent`, runs in the extension) | `POST /bookings {booking_date}` + local notification | No |
| Siri "Track my shuttle" (`WhereIsMyShuttleIntent`, LiveActivityIntent) | `GET /tracking/next` → starts Live Activity | No |
| Trip mode (`TripMonitor`) every 15s | `POST /users/1/location`, `GET /tracking/next`; Rebook → `POST /bookings/{id}/move` | No |
| Ask Clear Path chat / Siri "Ask Clear Path", simple requests (F14) | on-device Foundation Models classify → structured `POST /bookings {booking_date}` / `reschedule` / `cancel` / `GET /bookings`, then `POST /assistant/on-device-turns` | On-device only |
| Ask Clear Path chat / Siri "Ask Clear Path", everything else | `POST /assistant/messages` (tool-calling agent), `GET /assistant/conversations/{id}` | Yes |
| Share sheet / Home → Import work schedule (`ClearPathShare` extension, `ScheduleImport/`) | on-device OCR + Foundation Models → `POST /schedule/plan` → review → `POST /schedule/apply` (typed days only) | On-device only |
| Home → Your commute, habit reminder **Book** (F10) | `GET /habits` after each rides load → donations + local reminders; `POST /bookings {booking_date}`; `POST /habits/pin` | No |
| Claude Desktop | stdio MCP → `app.mcp_server` → same tools | (client's LLM) |
| Natural-language `POST /bookings {message}` | booking graph with Gemini intent extraction | Yes (legacy path) |

## Why things are the way they are (key decisions)

- **No APNs** (no paid developer account): Live Activities count down from
  absolute ETAs on-device; trip mode keeps the app alive with background
  location to poll and post local notifications.
- **Primary model `gemini-3.5-flash-lite`**, fallbacks
  `[gemini-3.5-flash-lite, gemini-3.1-flash-lite]`, 8s deadline per attempt:
  measured latency/quotas on the free tier (see AI.md).
- **Trip simulator**: real shuttles aren't moving during a demo; any booking
  can be replayed "now" at a chosen speed with injected delays and walk time.
- **Local embeddings** (fastembed `BAAI/bge-small-en-v1.5`, 384-d) in
  pgvector: free, private, fast.
- **Self-hosted Langfuse** (user's choice A): nothing leaves the Mac,
  telemetry off.
- **Shared/** folder compiled into app and widget extension so one-tap
  intents and API client are identical in both.
