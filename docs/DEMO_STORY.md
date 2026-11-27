# Demo story

**Title:** Hey Siri, Welcome to the Agentic Era
**Subtitle:** Engineering Proactive Mobile Experiences with Agentic AI and Native iOS

Internal technical knowledge-sharing session at BUsoft Tech (Chennai),
Thursday 3 December 2026 (moved from 17 November), for developers, QA engineers, BAs, managers and
tech leads. Live demo on the iPhone and the Mac.

This file is the overview. The words for every slide are in
[DEMO_SCRIPT.md](DEMO_SCRIPT.md) (the source of truth, and the deck's
speaker notes); how to run it, step by step, is in
[DEMO_RUNBOOK.md](DEMO_RUNBOOK.md). Deck:
https://claude.ai/artifact/HZYoYJ5KyrqThf3Z7GCKmZ (25 slides; private
until shared). All facts were checked against the
code on 2026-11-07/08. On 2026-11-24 the deck was cut from 53 slides to 22
around 22 demo steps: explanation slides were merged into their demo
slides, the prompt-injection demo and the lessons-learned slide were
dropped, and production and roadmap became one slide. The AI terms
glossary then moved up to slide 3, followed by an iOS terms slide. On
2026-11-27 slide 22 was added: redBus answering Siri without the app
name on iOS 27, and the APIs behind it.

## What the session must convey

1. An app built with current AI and iOS technology.
2. Each technology used for a product reason, not for its name.
3. Failures, fallbacks, alternatives, evaluation and UX all considered.
4. Testing and evaluation matter as much as building.
5. Why apps like this are still rare: Siri and AI aren't fully reliable.
6. A mobile developer learning AI, showing what's been learned, still
   learning.
7. What a production deployment would change, and how.
8. One connected story: each capability shown as a user experience first,
   then what happened, how it works, and the engineering decision behind it.

## How it's told

- **Opens with a single Siri request** ("book my usual shuttle with Clear
  Path"), then answers the audience's natural questions about it: how Siri
  knew the app, how it understood the request, which date, what "usual"
  means, and whether it needed an LLM.
- **Each capability follows from the previous one**: the request → the
  booking backend → learned habits and their reasons → user control →
  widgets, Control Center and the reminder → schedule changes → the
  commute in real time → the first question that needs reasoning → external
  AI → failure on purpose → testing → limitations → architecture → full
  scale.
- **One slide per step**: each demo slide carries its own "under the hood"
  (flow, iOS and backend points, badge), so there are no separate
  explanation slides.
- **Three badges** on every technical slide: **No AI** (deterministic
  code), **On-device AI** (Apple's models on the iPhone), **Cloud AI**
  (Gemini through the LangGraph agent; Claude Desktop as an external
  client).
- **Live, with honest failures**: natural failures are explained (Siri
  routing, free-tier latency); one is caused on purpose (a cloud AI
  outage). Prompt-injection defences are mentioned on the import slide and
  in the prepared Q&A, without a demo.
- No "Act" naming; plain technical section titles.

## Structure

| # | Slide | Live steps (runbook step) |
|---|---|---|
| 1 | Hey Siri, Welcome to the Agentic Era | Cold open: Siri books tomorrow, Earlier → Later (1) |
| 2 | Not a chat box inside an app | (who I am, the idea, live failures, the three badges) (2) |
| 3 | AI terms in plain English | (eight AI words: LLM, agent, tool, RAG, MCP, on-device model, eval, trace) (2) |
| 4 | iOS terms in plain English | (eight iOS words: App Intent, App Shortcut, Shortcuts app, widget, control, Live Activity, share extension, Foundation Models) (2) |
| 5 | What just happened? | (App Intents, the backend, BookingService, no LLM) (2) |
| 6 | What "my usual" means | Your commute card (3) |
| 7 | Why the 7:15? It tells you, and you can change it | Siri books Monday's learned 7:15; pin and unpin (4, 5) |
| 8 | Book without opening the app: widgets, Control Center and notifications | Widgets, Control Center → "Already booked"; reminder → Book (6, 7) |
| 9 | When the week changes | Share the schedule photo → review → Apply (8) |
| 10 | Your commute, live | Map, trip mode, Live Activity, time to leave, Siri tracking (9) |
| 11 | A delay, and a better shuttle | Delay → Rebook (10) |
| 12 | When AI needs to think | Siri "Should I leave now?": agent, tools, MCP weather (11) |
| 13 | One conversation, and not every message needs the cloud | Chat shows the Siri turn; on-device commands (12) |
| 14 | Answers with sources | Voice → "Why can't I book Saturday?" → RAG (13) |
| 15 | Goals instead of times | Meeting at 8; Tuesday by 7:30, the honest no (14) |
| 16 | Booking from Claude Desktop | MCP in; Saturday refused (15) |
| 17 | The cloud AI goes down | Outage on: what still works (16) |
| 18 | Tracing every turn | Langfuse; outage off (17) |
| 19 | How I know it works | (three layers of checking, one evaluation) (18) |
| 20 | What evaluations caught | (baseline, four bugs) (18) |
| 21 | Why apps like this are still rare | (the failure count; Siri, model and platform limits) (19) |
| 22 | Siri is catching up: iOS 27 | redBus answers “Where’s my bus pickup point?” with no app name; Clear Path still needs it; intent schemas, indexed entities, screen awareness (20) |
| 23 | Architecture: from iPhone to Gemini | (everything from the iPhone through Docker to Gemini; five rules) (21) |
| 24 | From prototype to full scale | (changes for full scale, cost, focus next) (22) |
| 25 | What this means for our projects | (the pattern, the closing line, questions) (23) |

About 55 minutes plus questions.

## Demo day assumptions

Thursday demo, so "tomorrow" is Friday and weekday names mean next week's
day. `reset_demo_db` run in the demo week (ride history is placed relative
to the current week), the saved usual restored to the 7:30, and next
Tuesday (8 December) booked beforehand. Steps that named Friday on a
Tuesday (Claude Desktop, the outage cancel and rebook) use next Thursday,
so they never touch tomorrow's trip booking; the schedule import then
cancels two days (Tuesday WFH and the reminder's Thursday booking). Learned
usuals: Mon 7:15, Tue 7:30, Wed 7:30 (overall pattern), Thu 8:00, Fri 7:30.
The booking chain, the trip clock (the delay must come within about 8.5
minutes of starting the simulated trip) and every command are in the
runbook.

## From prototype to production

The message: *"I know what I built, I built it this way for reasons, and I
know what a real deployment changes and how."*

**Users and security**

| Today (and why) | In production | How |
|---|---|---|
| One rider, user id 1 on every request (keeps the demo about the AI) | Many riders, many companies | Sign in with Apple or company SSO (OIDC); the user comes from a verified token, never from the request body; tenants per company with their own routes and rules |
| Plain HTTP to the Mac's Wi-Fi address | Secure public API | HTTPS everywhere, an API gateway with rate limits, secrets in a secrets manager |
| MCP server runs locally as user 1 | AI clients acting for real users | Remote Streamable HTTP MCP with OAuth, per-user scopes, an audit log, confirmation for destructive tools |
| Location and habits stored in a demo database | Personal data | Consent, retention limits, deletion on request, India's DPDP Act |

**Platform and scale**

| Today (and why) | In production | How |
|---|---|---|
| uvicorn on a laptop; only Postgres in Docker | Always-on service | Containerised backend on a managed platform with autoscaling and health checks; staging and production environments |
| Tables created by `create_all`; demo reset scripts | Safe schema changes | Versioned migrations (e.g. Alembic), backups, managed Postgres with pgvector |
| One agent session with a tool lock (one DB session) | Many concurrent users | A session per request, async I/O, a job queue for slow work, idempotency keys on booking writes, a cache for read-heavy data |
| Simulated trips on an illustrative route | Real fleet | Vehicle GPS or a transit feed, road-snapped routes, an ETA model, operator tools |

**Mobile**

| Today (and why) | In production | How |
|---|---|---|
| No push (free developer account) → trip mode keeps the app awake with background location | Server-driven alerts, better battery | APNs for delay and time-to-leave alerts; push-to-start and push-updated Live Activities; trip mode only as a fallback |
| Siri phrases tuned by hand | Broader, sturdier voice access | More App Intents and App Entities, Smart Stack relevance, Shortcuts actions |
| On-device AI only where Apple Intelligence runs | Every supported device | Keep the rules and cloud fallbacks; measure on-device accuracy on real devices; more on-device intents |
| English only; one app | Wider audience | Localisation (Indian languages for speech and RAG), accessibility review, an Android version with the same backend |

**AI quality and cost**

| Today (and why) | In production | How |
|---|---|---|
| Free-tier Gemini Flash-Lite, chosen by measured latency; fallbacks within one provider | Reliable latency and quota | Paid tier with an SLA; fallback across providers (e.g. Gemini, Claude, OpenAI) behind one interface; choose each model by evals, not by name; per-user budgets |
| 16 policy sections, small local embedding model | Large, changing knowledge base | Document ingestion pipeline with versioning, hybrid search (keywords + vectors), a reranker, retrieval evals |
| Evals run by hand (no CI, by choice) | Quality gate on every change | Run `evals.run --check` in CI on every prompt or model change; nightly full runs; turn real failing conversations from traces into new eval cases |
| Langfuse self-hosted on a laptop | Monitoring and alerts | Dashboards for latency, cost and error rate, alerts, crash reporting on the app |
| Prompt-injection defences on schedule import | Defence everywhere | Treat every external text as data, confirmations for mutating agent actions, red-team evals, abuse rate limits |

**Cost at scale (estimate, not a measurement):** at the baseline's
~$0.002 per AI task, 1,000 riders × 4 cloud AI requests a day ≈ $8 a day.
Structured requests and on-device chat cost nothing per request.

**Roadmap:** now, more on-device commands and re-saving the 36-scenario
baseline after the prompt fixes; next, push, Smart Stack relevance and evals in CI; later,
sign-in and many riders, real transit data, cross-provider fallback and
on-device model evals.
