# Demo story

**Title:** Hey Siri, Welcome to the Agentic Era
**Subtitle:** Engineering Proactive Mobile Experiences with Agentic AI and Native iOS

Finalised 2026-11-07. Every step, string and number below was checked
against the code (iOS and backend) on 2026-11-07; quoted strings are the
app's own. Exact setup commands live in [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md).

## The talk at a glance

- **Audience:** BUsoft Tech (Chennai): devs, QA, BAs, juniors to seniors,
  managers and tech leads across domains. Engineering depth sits on the
  "under the hood" slides; the story itself is plain English.
- **Length:** about an hour plus Q&A; not time-boxed.
- **Live first.** Siri and AI aren't fully reliable yet, and we say so up
  front. A natural failure is explained (how and why); a few failures are
  caused on purpose (Act 5) to show how they're handled.
- **What it must convey:**
  1. An app built with current AI and iOS technology.
  2. Each technology used for a product reason, not for its name.
  3. Failures, fallbacks, alternatives, evals and UX all considered.
  4. Testing and evals matter as much as building.
  5. Why apps like this are still rare: Siri and AI aren't 100% reliable.
  6. A mobile developer learning AI, showing what's been learned, still
     learning.
  7. What a real production deployment would change, and how (Act 9).
  8. One story, with the engineering explained after each request, ending
     in the full architecture.
- **Format of every step:** do it live → one "Under the hood" slide with a
  badge for where the work ran (⚪ **No AI** · 🟢 **On device** ·
  🔵 **Cloud AI**), what iOS does, what the backend/AI does, and what
  happens if it fails.
- **Slides:** clean and professional, one idea per slide, large type, few
  words, light theme with one accent colour plus the three badge colours.
  Detail goes in speaker notes.

## Demo day: Tuesday

The bookings below chain together on a Tuesday ("tomorrow" = Wednesday).
Prep (details in the runbook):

1. `python -m scripts.reset_demo_db` → learned usuals: Mon 7:15 (4 of
   last 5 Mondays), Tue 7:30 (each of last 5), Wed 7:30 (6 of last 10
   rides), Thu 8:00 (4 of last 5 Thursdays), Fri 7:30 (each of last 5).
2. Book **next Tuesday** so the schedule import has a booking to cancel.
3. Schedule samples for next week (`run.sh sample`, with and without
   `--injection`) saved to Photos.
4. App installed from Xcode as a **Debug** build ("Preview reminder" is
   Debug-only), then launched from the home-screen icon.
5. `llm_outage` off, Langfuse open, Claude Desktop with the clear-path MCP
   server, phone mirrored over a cable.

Booking state through the demo: tomorrow (Wed) 7:30 → Thu 8:00 (reminder)
→ next Mon 7:15 (Siri) → import: Mon keep, Tue cancel, Wed book →
Wed rebooked to 7:45 (delay) → next Mon moved to 7:00 (on device) → Wed
moved to 7:15 (goal) → Fri booked (Claude Desktop) → Fri cancelled on
device and rebooked by Siri (outage).

---

## Prologue

**P1. Cold open.** Lock Screen: "Hey Siri, book my usual shuttle with
Clear Path" → "Done. You're on the 7:30 AM shuttle tomorrow, arriving at
Office by 8:15 AM. That's your usual: …" → tap **Earlier**, then **Later**
(back to the 7:30, which Act 2 needs). *"Hold that thought."*

**P2. Title slide.**

**P3. Who I am.** A mobile developer learning AI. Brought / Learned:
App Intents, widgets, Live Activities, Swift concurrency → agents, tools,
RAG, MCP, evals, tracing, on-device models.

**P4. The idea.** Not a chat box inside an app: the AI works through
Siri, widgets, notifications, the Lock Screen and the share sheet. The app
is where you go only when you want to.

**P5. Five design rules.**
1. Facts stay deterministic: the database is the source of truth; the AI
   never invents bookings, times or availability.
2. Tools act; the AI only chooses which one.
3. Structured requests (Siri phrases, buttons) skip the AI.
4. Cheapest model that measurably works, decided with evals.
5. Be honest when something fails.

**P6. How it all runs** (one diagram).
- iPhone app with three targets: app, widget extension, share extension.
  Calls the backend over Wi-Fi at the Mac's address
  (`BOOKING_API_BASE_URL`).
- Backend: FastAPI (Python) on the Mac via uvicorn (not in Docker).
- Docker: one Postgres + **pgvector** container (bookings, agent memory,
  policy embeddings); six containers for self-hosted **Langfuse** (web,
  worker, ClickHouse, MinIO, Redis, Postgres).
- AI: on the iPhone, Apple's on-device model, Vision OCR and speech
  recognition; in the cloud, Gemini Flash-Lite (free tier) through a
  LangGraph agent; small local MCP servers.

**P7. AI in plain English.** LLM, agent, tool, RAG, MCP, on-device model,
eval, trace: one line each with a shuttle example.

**P8. Meet the rider.** One rider (Godwin), Home → Office. Shuttles 7:00,
7:15, 7:30, 7:45, 8:00; 45 minutes; 10 seats. Rules, all in one
`BookingService`, in this order: past date → weekend → more than 14 days
ahead → closes 30 minutes before departure → full. A repeat request
returns the existing booking (not an error).

**P9. Ground rules.** *"This is live. Siri and AI aren't fully reliable
yet. If something fails, I'll show you why. A few failures I'll cause on
purpose."*

---

## Act 1: The evening before

**1.1 Habit card.** Home → **Your commute**: "Thu isn't booked yet",
"8:00 AM → arrives 8:45 AM", "You took it on 4 of your last 5 Thursdays";
expand **Your usual week** (sparkles = learned, circle = default).
- ⚪ iOS: `HabitCard` (SwiftUI) loads `GET /habits`.
- Backend: `HabitService` per weekday: pin → last 5 rides that weekday →
  last 10 rides → saved 7:30. A habit needs at least 3 rides and more
  than half the sample; only the last 8 weeks count. Plain statistics, so
  it can always explain itself.

**1.2 Habit reminder.** ••• → **Preview reminder** → lock the phone →
"Book Thursday's shuttle?" / "Your usual Thursday shuttle is the 8:00 AM,
arriving 8:45 AM — you took it on 4 of your last 5 Thursdays. You haven't
booked it yet." → long-press → **Book** → "Shuttle booked".
- ⚪ iOS: `HabitReminders` schedules a local notification at 7 PM the
  evening before each usual day not booked; **Book** calls
  `POST /bookings` in the background. Booking that day from Siri, the
  widget, the card or on-device chat withdraws the reminder.
- Design rule: it suggests; it never books by itself.

**1.3 Learned habit through Siri.** "Hey Siri, book my usual shuttle for
Monday with Clear Path" → the **7:15**, not the saved 7:30: "…That's your
usual: you took it on 4 of your last 5 Mondays."
- ⚪ iOS: App Intents. `AppShortcutsProvider` registers 9 booking phrases
  (Siri and the Shortcuts app know them without setup); `BookingDay` is an
  `AppEnum` (today, tomorrow, Monday–Sunday), which is how Siri fills in
  the day; `perform()` sends a structured `POST /bookings {booking_date}`.
  Bookings are donated with `IntentDonationManager` for Siri Suggestions
  and Spotlight.
- Backend: same rules, usual from `HabitService`. No LLM call.

**1.4 Schedule import.** Photos → next week's schedule → Share →
**Clear Path** → review: Monday **keep**, Tuesday WFH **cancel**,
Wednesday **book**, Thursday offsite and Friday leave need nothing.
Switch a row off and on; point at "Read on this iPhone with Apple
Intelligence" and "Text read from your document" → **Apply 2 Changes**.
- 🟢 iOS (inside the share extension): Vision `RecognizeTextRequest`
  OCR (images downscaled to 2,400 px, text capped at 3,000 characters;
  PDFs use their text layer or OCR of up to 3 pages) → `DocumentSafety`
  removes lines that look like instructions to an AI → **Foundation
  Models** with `@Generable` guided generation, so the model can only
  output `{weekday, date, kind}` → validation. If Apple Intelligence is
  unavailable, keyword rules take over and the label says why.
- Backend: `POST /schedule/plan` (office day → book / keep / blocked;
  other days → cancel / nothing) → `POST /schedule/apply`. It accepts
  only typed days; document text never leaves the phone.
- Also: Home → **Import work schedule** → Choose Photo / Choose File.

**1.5 Pin an override.** Card menu → "Always use the 8:00 AM" → pin
icon → "Learn from my rides again".
- Backend: `POST /habits/pin`; a pin beats what was learned.

---

## Act 2: The morning

**2.1 The cold open explained.**
- ⚪ iOS: the reply card is an App Intents **SnippetIntent**; **Earlier**
  and **Later** run `RescheduleBookingIntent` →
  `POST /bookings/{id}/reschedule`. A button is disabled when no
  neighbouring shuttle can be booked.
- *"No LLM. Structured requests don't need one."*

**2.2 One tap.** Home-screen widget shows tomorrow's ride (no **Book
tomorrow** button, because tomorrow is booked); Lock Screen widget;
Control Center button or **Action button** → notification "Already
booked".
- ⚪ iOS: WidgetKit `NextRideWidget` (small, medium, rectangular,
  inline); `BookShuttleControl` is a `ControlWidget` the user places in
  Control Center, on the Lock Screen or on the Action button. Both run
  `BookTomorrowIntent` in the widget extension and confirm with a local
  notification.
- Backend: the duplicate check returns the existing booking.

**2.3 Start the trip.** `python -m scripts.demo_trip` → app → **Where's
my shuttle** (map) → **Start trip mode** → lock → Live Activity on the
Lock Screen and in the Dynamic Island.
- ⚪ iOS: MapKit route and bus; the screen polls `GET /tracking/next`
  every 5 s. Trip mode: `CLServiceSession` +
  `CLBackgroundActivitySession` + `CLLocationUpdate.liveUpdates` keep
  the app running; every 15 s it updates the **ActivityKit** Live
  Activity (countdown, self-advancing progress bar); location is uploaded
  after moving 50 m or every 2 minutes.
- Backend: the simulator replays tomorrow's 7:30 "now" along an
  illustrative Bengaluru route. Say it's simulated.
- Why trip mode: push needs a paid Apple developer account.

**2.4 Time to leave.** "Your shuttle reaches … in N minutes. It's about a
4-minute walk to …" — a time-sensitive local notification, once, when
`leave_in_minutes ≤ 0`.

**2.5 Siri tracking.** "Hey Siri, track my shuttle with Clear Path" →
Siri speaks the status.
- iOS: `WhereIsMyShuttleIntent` is a `LiveActivityIntent`, so it can
  start the Live Activity from Siri.
- Lesson: spoken "Where's my shuttle…" is often answered by Siri itself;
  lead with "Track my shuttle".

**2.6 Ask the agent through Siri.** "Hey Siri, ask Clear Path" → "What
would you like Clear Path to do?" → "Should I leave now?" → yes/no plus
the weather.
- 🔵 iOS: `AskClearPathIntent` tries the on-device assistant first; this
  question doesn't qualify, so it goes to `POST /assistant/messages`.
- AI: a **LangGraph** loop (model picks a tool → tool runs → model sees
  the result; up to 12 steps). `get_shuttle_status` returns `leave_now`
  **computed in code** (evals caught the model saying "yes" with 11
  minutes to spare). Weather comes from **an MCP server I wrote**
  (Open-Meteo, no key); the backend starts it at launch and wraps its
  tool for the agent. Models: Gemini 3.5 Flash-Lite → retry → 3.1
  Flash-Lite, 8 seconds each.

**2.7 Delay → Rebook.** Within about 8 minutes of starting the trip:
`python -m scripts.demo_trip --delay 20` → Lock Screen badge "20 min
late", orange bar → "…running 20 minutes late. The 7:45 AM shuttle still
gets you to Office by 8:30 AM, 5 minutes sooner. Rebook?" → **Rebook** →
"Rebooked" (**Keep** just dismisses).
- ⚪ iOS: a notification category with actions; Rebook calls
  `POST /bookings/{id}/move` without opening the app.
- Backend: the trip planner picks the catchable shuttle that arrives
  soonest. The Dynamic Island has no badge; its bar turns orange.

**2.8 Shared memory.** App → **Ask Clear Path** → the Siri conversation
is already there, with "Checked the weather · via weather MCP server".
- Backend: LangGraph `PostgresSaver`, thread `user:conversation`; the
  phone keeps the conversation id for 30 minutes after the last message,
  shared by Siri and the chat.

---

## Act 3: Chat, used on purpose

**3.1 On device.** "What do I have booked?" → **"On device · Apple
Intelligence"**; "Move Monday earlier" → the 7:00, also on device.
- 🟢 iOS (`OnDeviceAssistant`): rules gate (≤100 characters / 14 words,
  no digits, no question/condition words, exactly one action word, a day
  for any change) → Apple's on-device model classifies with
  `@Generable` within 3 s → **must agree with the words** → structured
  endpoint. Any doubt → cloud. The turn is recorded with
  `POST /assistant/on-device-turns`.

**3.2 Voice + RAG.** Tap the mic → "Why can't I book Saturday?" → the
rule plus a **cited** Booking Policy passage.
- 🟢 iOS: `SpeechAnalyzer` + `SpeechTranscriber` on device, tuned for
  "Clear Path" and "shuttle".
- 🔵 AI: `check_booking_eligibility` (rule code) → `search_policies` =
  **RAG**: 16 policy sections embedded locally (bge-small, 384
  dimensions) in pgvector with an HNSW index; below 0.60 similarity is
  ignored; only the top match is cited, and only at 0.70 or above. The
  prompt allows policy answers only from search results.

**3.3 Goal booking.** "I have a meeting at 8 tomorrow, get me there in
time" → "Booked your trip plan": 7:45 → **7:15, arriving 8:00 AM**.
- 🔵 + ⚪ The model only extracts the date and arrive-by time; a
  **deterministic trip planner** picks the shuttle. Evals: 4/9 → 9/9
  after the planner (before it, the agent booked impossible trips).

**3.4 The honest no.** "Get me to the office by 7:30 on Friday" → "No
shuttle gets you there by 7:30 AM. The soonest is the 7:00 AM, arriving
7:45 AM (15 minutes late)." Nothing is booked.

**3.5 What the chat shows.** Action rows (green check / orange ✗ with the
error), sources, "New conversation". *"Every reply shows what was
actually done."*

---

## Act 4: At the desk (MCP both ways)

**4.1** Claude Desktop: "Book my usual shuttle for Friday" → permission →
booked → refresh the iPhone.
- `app.mcp_server` publishes **13 tools** (the agent's 12 plus
  `get_today`) over stdio; tools are annotated read-only or changing, and
  `cancel_booking` destructive.

**4.2** "What's my usual Thursday?" → 8:00 with its reason. "Book Saturday
too" → "Shuttles don't run on Saturdays."
- *"Another company's AI, held to the same rules. MCP both ways: my app
  is a tool for any AI, and my agent uses other MCP tools."*

---

## Act 5: Failures on purpose

**5.1 Prompt injection.** Share the injection sample → orange "Ignored 1
line that looked like instructions to an AI" → only the real days are
proposed. Five layers: lines removed on the phone → model told the
document is data, no tools → output limited to typed days → server
accepts only `{date, kind}` → nothing changes until **Apply**.

**5.2 Cloud AI down.** `python -m scripts.llm_outage on` (no restart) →
`/health` shows `"llm":"outage"` → chat "Why can't I book Saturday?" →
"Clear Path's assistant is unavailable right now. Bookings still work:
say "Book my usual shuttle with Clear Path", or use the widget." A flag
file swaps in models that fail immediately; the real fallback chain still
runs all three attempts, then an honest 503.

**5.3 Still working.** Chat "Cancel Friday" → **On device** ✓; "Hey
Siri, book my usual shuttle for Friday with Clear Path" ✓. *"The AI is an
enhancement, not a single point of failure."*

**5.4 The trace.** Langfuse → the failed turn is an **ERROR** trace with
every attempt → `python -m scripts.llm_outage off`.
- Slide only: if a booking changed before the AI failed, the reply is "I
  made changes to your bookings but couldn't finish replying. Check your
  rides to see the latest." It never hides a real change.

### If something fails naturally

| What fails | What the audience sees | Explain |
|---|---|---|
| Siri doesn't run the intent | Siri answers itself | iOS 27 Siri routes with its own model; App Shortcut phrases are a hint, not a guarantee. Retry with Type to Siri |
| Gemini slow or rate-limited | "Working on it…", then an answer or the 503 | Free tier per-minute limits; 8 s per attempt, three attempts |
| On-device model declines | No "On device" label; the cloud answers | The model must agree with the rules gate; any doubt goes to the cloud |
| Backend unreachable | "I couldn't reach Clear Path. Check your connection and try again." | Phone and Mac must share Wi-Fi; every surface reports it plainly |
| Delay offers no alternative | Delay notice without Rebook | The alternative must still be catchable (started too late) |

---

## Act 6: How I know it works

- **Tests:** about 150 pytest cases (isolated `_test` database, frozen
  clock, no network, ~6 s) and 76 Swift Testing tests (~107 cases with
  arguments) plus 2 UI tests.
- **Evals:** 36 scenarios (goal 9, rules-RAG 8, booking 7, tracking 5,
  follow-up 3, habit 3, safety 1). Each checks tools called and not
  called, final bookings, sources, and an AI judge score (1–5).
- **Saved baseline (33 cases):** 32/33, tool accuracy 100%, judge 4.94,
  0 hallucination flags, p50 5.5 s, p95 22.6 s, about $0.0017 per task at
  list prices (free tier, nothing billed).
- **What evals caught:** goal booking 4/9 → 9/9; invented habit history;
  FAQ not found for "colleague"; "yes, leave now" with 11 minutes to
  spare.
- **Evaluating the evaluator:** the judge once read the pickup time as the
  arrival time; hard checks come first.
- **Langfuse live:** a normal turn (model calls, tool spans), an
  `on-device` trace, eval traces with scores.
- **On-device extraction eval:** keyword rules 11/15, injection cases 4/4
  safe; the on-device model isn't measured (Apple Intelligence can't run
  on the Mac). An honest gap.

---

## Act 7: Why we don't see many apps like this yet

| Real limit we hit | What the code does |
|---|---|
| iOS 27 Siri sometimes misses exact phrases or answers itself | Tested phrases; one intent with an optional day; Type to Siri |
| Siri misheard the app name | Alternative names "ClearPath", "Clear Path Shuttle", "Clear Footpath" |
| Siri can drop the day | No day on a Fri/Sat: "Shuttles don't run on Saturdays. Which day should I book?" |
| On-device AI isn't on every device | Keyword rules or the cloud, and the label says which ran |
| No push without a paid account | Trip mode with background location |
| Free-tier limits; p95 22 s | 8 s deadlines, fallback chain, paced evals |
| Model replied with a tool name instead of a sentence | Rejected; next model tried |
| AI judges miscount | Hard checks first; the judge grades wording only |
| First tap on the chat box stalled for seconds | Keyboard prewarmed on Home |

Plus anything that failed live today.

---

## Act 8: The full architecture

Built up as a recap: iOS surfaces → structured requests straight to
services, AI requests to the agent → one `BookingService` with all the
rules → Postgres + pgvector → MCP in and out → Langfuse and evals. Finish
on "Where the AI runs": ⚪ / 🟢 / 🔵 for every feature.

---

## Act 9: What's next

### 9.1 What I learned

The mobile-to-AI journey: what carried over from mobile engineering, what
was new (agents, RAG, MCP, evals), and what surprised me (how little the
LLM does, and how much evals and honesty matter).

### 9.2 From demo to production

The message: *"I know what I built, I built it this way for reasons, and I
know what a real deployment changes and how."* One slide per row group,
three columns: **Today (and why)** · **In production** · **How**.

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
| Siri phrases tuned by hand | Broader, sturdier voice access | More App Intents and App Entities, Smart Stack relevance, Shortcuts actions; follow Apple Intelligence's App Intents improvements |
| On-device AI only where Apple Intelligence runs | Every supported device | Keep the rules and cloud fallbacks; measure on-device accuracy on real devices; more on-device intents |
| English only; one app | Wider audience | Localisation (Indian languages for speech and RAG), accessibility review, an Android version with the same backend |

**AI quality and cost**

| Today (and why) | In production | How |
|---|---|---|
| Free-tier Gemini Flash-Lite, chosen by measured latency; fallbacks within one provider | Reliable latency and quota | Paid tier with an SLA; fallback across providers (e.g. Gemini, Claude, OpenAI) behind one interface; choose each model by evals, not by name; per-user budgets |
| 16 policy sections, small local embedding model | Large, changing knowledge base | Document ingestion pipeline with versioning, hybrid search (keywords + vectors), a reranker, retrieval evals (did we find the right passage?) |
| Evals run by hand (no CI, by choice) | Quality gate on every change | Run `evals.run --check` in CI on every prompt or model change; nightly full runs; turn real failing conversations from traces into new eval cases; user thumbs up/down |
| Langfuse self-hosted on a laptop | Monitoring and alerts | Managed or hosted tracing, dashboards for latency, cost and error rate, alerts, crash reporting on the app |
| Prompt-injection defences on schedule import | Defence everywhere | Treat every external text as data, confirmations for mutating agent actions, red-team evals, abuse rate limits |

**Cost at scale (estimate):** at the baseline's ~$0.0017 per AI task, 1,000
riders × 4 AI requests a day ≈ $7 a day. Structured requests (Siri
phrases, widgets, on-device chat) cost nothing, which is why "AI only
where it earns its place" is also a cost decision.

### 9.3 Roadmap

- **Now:** more on-device requests (e.g. "book the 7:15 on Friday"), a
  clean 36-case eval baseline.
- **Next:** push notifications, Smart Stack relevance, evals in CI.
- **Later:** the production changes above: sign-in and many riders, real
  transit data, provider fallback, on-device evals.

### 9.4 For BUsoft

The same pattern fits client apps in any domain: structured actions
first, AI where it earns its place, evals as part of QA, honest failures.

### 9.5 Close

*"The AI isn't a chat box inside the app. It works through the parts of
iOS people already use. That's the agentic era, and it's still being
engineered."* Then Q&A.
