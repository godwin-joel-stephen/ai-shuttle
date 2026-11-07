# Product: Clear Path

## Goal

Show, in a live demo, the ability to build a *practical* AI-powered mobile
app — not "a chatbot inside an app with voice". The AI works through the
surfaces iOS users already use (Siri, notifications, widgets, Control
Center, Action button, Lock Screen, Dynamic Island, share sheet), with a
production-grade backend: tool-calling agents, RAG, MCP, evaluation,
tracing, on-device AI.

Closing line of the demo: *"The AI isn't a chat box inside the app. It works
through the parts of iOS people already use, and the app is only where you
go when you want to."*

## Scope decisions

- **Single user** (the presenter, "Godwin Joel", user id 1), commuting
  Home → Office. The original "Emma / child" scenarios were dropped to keep
  the demo simple; adapt any Emma flow to the rider's own commute.
- In-app chat is **secondary**: used where conversation genuinely fits
  (troubleshooting with citations, unusual requests, activity log).
- Every technology must be justified by a product capability (from the
  original planning docs, which live outside the repo: IDEA,
  IMPLEMENTATION-PLAN, LLM architecture).
- Nothing paid without the user's agreement (free-tier Gemini, self-hosted
  everything). No paid Apple developer account, so **no APNs push**; trip
  mode (background location) replaces push.

## Flows

Legend: ✅ done and verified on device · 🟡 partial · ⏳ not started

| # | Flow | Surface | Status |
|---|---|---|---|
| F1 | "Book my usual shuttle (for Friday) with Clear Path"; Siri card with Earlier/Later buttons | Siri | ✅ |
| F2 | One-tap booking: home/Lock Screen widget, Control Center control, Action button | Widgets | ✅ |
| F3 | Import a work schedule (office / home / offsite / leave days) from a photo, screenshot, PDF or text via the share sheet or Home → Import work schedule: Vision OCR + on-device Foundation Models → typed days → server plans book/cancel with the booking rules → review → **Apply** | Share sheet | ✅ (verified on iPhone 2026-11-05) |
| F4 | Proactive delay alert: "Shuttle 20 min late… the 7:45 gets you there 5 min sooner. [Rebook] [Keep]" — Rebook works from the notification | Notification | ✅ (alternative chosen by the F7 trip planner's option logic) |
| F5 | "Time to leave" alert and "Should I leave now?" using walking time (+ weather via MCP) | Notification / chat | ✅ |
| F6 | Live tracking: Siri "Track my shuttle with Clear Path", Live Activity (Lock Screen + Dynamic Island), live map | Siri / Live Activity | ✅ |
| F7 | Goal-based booking ("get me to the office by 8:30", "I have a meeting at 8", "by 8 every day this week", "will I make it by 8:20?") via a deterministic trip planner the agent calls (`plan_trip` / `book_trip_plan`) | Chat / Siri Ask Clear Path / MCP | ✅ (tested on iPhone 2026-11-07) |
| F8 | "Why can't I book Saturday?" — real rule + RAG over policies, cited sources | Chat / Siri | ✅ |
| F9 | Ask Clear Path chat + on-device voice + Siri "Ask Clear Path", shared memory, activity log | Chat / Siri | ✅ |
| F10 | Learned habits: "usual" is learned per weekday from recent rides ("you took the 7:15 on 4 of your last 5 Mondays") and explained wherever it's used; pin to override. Every booking is donated (Siri Suggestions/Spotlight); an evening-before reminder with a **Book** button for usual days not yet booked; Home → Your commute card. Never books by itself | Lock Screen / Spotlight / notification / Siri | ✅ merged 2026-11-07 (chat path verified on iPhone; rest of device checklist in PROGRESS.md) |
| F11 | MCP server: book from Claude Desktop with the same rules | Laptop | ✅ (verified in Claude Desktop) |
| E | Agent uses an external MCP server (weather) | Chat | ✅ |
| F12 | Evaluation harness + Langfuse tracing/dashboard | Laptop | ✅ (no CI by user choice) |
| F13 | Reliability demo: "LLM off" → Siri booking still works; prompt-injection checks for imported documents | Siri | ✅ `scripts.llm_outage on\|off` flips a live simulated outage; structured surfaces keep working, the chat/Ask Clear Path answer an honest 503 that points to Siri booking; error trace in Langfuse; imported documents are screened (F3); runbook step 10 (merged 2026-11-07) |
| F14 | On-device routing: simple chat / "Ask Clear Path" requests (book usual, move earlier/later, cancel, what's booked — with a named day) answered on the iPhone by Apple's on-device model + structured endpoints, labelled "On device"; cloud agent for everything else; recorded in the shared conversation; works during an LLM outage | Chat / Siri | ✅ merged 2026-11-07 (verified on iPhone) |

## Demo order (planned)

1. Siri: "Book my usual shuttle with Clear Path", tap **Earlier** on the Siri card (F1)
2. Widget / Control Center one-tap booking (F2)
3. Share sheet: schedule import from a photo of the week's schedule → review → Apply (F3); optionally the version with injected fine print
4. Proactive delay alert → Rebook from the notification (F4)
5. "Time to leave" alert (F5)
6. Siri "Track my shuttle" → Live Activity (F6)
7. Habit reminder "Book Monday's shuttle? … you took it on 4 of your last 5 Mondays" → **Book** from the notification (F10)
8. Open the app: everything already reflected; chat used on purpose for "Why can't I book?" with citations (F8), optionally goal booking (F7)
9. Laptop: Claude Desktop books through MCP; agent's weather step labelled "via weather MCP server" (F11 + E)
10. Laptop: Langfuse trace of a turn, evaluation results (F12); "LLM off" reliability (F13)
11. Architecture slide

See [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md) for exact commands.

## Design principles

- Deterministic facts stay deterministic: PostgreSQL + services are the
  source of truth; the LLM never invents bookings, times or availability.
- Tools act; the LLM chooses. Business rules live in services and apply to
  every client (Siri, widgets, chat, MCP).
- Structured requests (Siri phrases, widget buttons) skip the LLM entirely.
- Cheapest model that measurably meets requirements; decide with evals.
- Be honest in failure: never report "unavailable" when a booking changed.
