# Progress

Last updated 2026-11-07. All work through F10 (learned habits) is merged
into `main` and pushed. **F13 — reliability demo** is built on
`feature/f13-reliability` and awaits the iPhone check (below).

## Done (verified on the user's iPhone unless noted)

| Phase | Commits (newest first within phase) | Notes |
|---|---|---|
| F1 Siri booking, single-user backend | 6ad1210 | booking rules, duplicate protection, natural confirmations, Siri card Earlier/Later |
| F2 widgets, Control Center, Action button | 6ad1210 | widget extension added by editing project.pbxproj |
| Test DB isolation | 586cf41, 80ad919 | second fix after a regression (see Known issues history) |
| Agent + memory | 8dc1423 | LangGraph tool agent, PostgresSaver, fallback, partial-failure honesty |
| Ask Clear Path chat, voice, Siri ask | 7e9c997 | SpeechAnalyzer, shared conversation |
| F8 RAG | 2b1f9dd, bbda162 | rules + pgvector + citations |
| F6 tracking | d88f268, 5dc6603 | simulator, Live Activity, map, Siri "Track my shuttle" |
| F4/F5 trip mode | bc9fb5f, 44736dd, 0b3da67, 891db65, 027418e | background location, local notifications, Rebook, walk time, model latency fix |
| F11/E MCP | 569efb9, 7fd6d81, 6125dec | verified in Claude Desktop 2026-11-04 |
| F12 evals + Langfuse | 4045638, 2ffc947, 52116d8 | baseline 22/24; self-hosted Langfuse |
| Config | c4363e3, see git log | backend address (now 192.168.1.6, changed 2026-11-07) |
| F7 goal planning | 544da0a | deterministic `TripPlanner` + `plan_trip`/`book_trip_plan` tools; F4 alternative reuses it; 9 goal eval cases (4/9 → 9/9); full eval 32/33 saved as baseline; tested on iPhone 2026-11-07 |
| F10 learned habits | e7301b4, 245144d | `HabitService`: usual per weekday from the last 5 rides that weekday → last 10 rides → saved 7:30; pin overrides; reason travels to Siri/chat/notifications. `/habits`, `/habits/pin`, `get_commute_habits` / `set_usual_shuttle` tools, demo ride history in `reset_demo_db`. iOS: donations after every rides load, evening-before reminder with **Book**, Home → Your commute card. 19 backend + 9 Swift tests; habit evals 3/3. Merged 2026-11-07 at the user's request. On iPhone so far: in-app chat books the learned 8:00 Thursday with its reason; two issues found and fixed in 245144d (Siri dropping the day on a weekend, garbled model reply). Rest of the device checklist below is still to report |
| F3 schedule import | 1d7fe8f | share extension + in-app import, on-device OCR + Foundation Models, `/schedule/plan` + `/apply`, injection screening, extraction eval; verified on iPhone 2026-11-05 (share sheet, injection sample, in-app import) |

## Current phase: F13 — reliability demo (built, awaiting iPhone check)

Branch `feature/f13-reliability`, not merged yet. Built 2026-11-07:
- `python -m scripts.llm_outage on|off` (runtime flag file
  `backend/.llm_outage`, gitignored; user's choice over env var + restart).
  `app/core/outage.py` holds the flag; `create_chat_model` / `create_llm`
  return failing stand-ins (`app/agent/outage_models.py`) while it exists,
  so the real fallback chain → 503 path runs with no network call.
  `GET /health` reports `"llm": "ok"|"outage"`.
- 503 wording points to what still works: assistant → "Clear Path's
  assistant is unavailable right now. Bookings still work: say "Book my
  usual shuttle with Clear Path", or use the widget."; natural-language
  `POST /bookings` → "…Try "Book my usual shuttle with Clear Path"."
  The iOS chat and Ask Clear Path already show/read the server `detail`,
  so no app change was needed.
- Langfuse: `traced` marks a failed turn's span `level=ERROR` with the
  exception as status message.
- 11 tests in `tests/test_llm_outage.py` (structured booking, Earlier/Later,
  habits keep working; assistant + NL booking 503 with nothing booked;
  every fallback model tried; health; error trace). The `outage_flag`
  autouse fixture points the flag at a temp file in tests.
- Verified live on a temporary uvicorn (port 8001): flag flips without a
  restart; assistant 503 in 0.3s.
- DEMO_RUNBOOK step 10 + pre-demo check 12; BACKEND/AI/PRODUCT updated.

Still to do: iPhone check (see the test steps given 2026-11-07), Langfuse
error trace check, then merge when the user asks. Not built (user's
choice): deterministic answers to simple chat requests during an outage
(stays with the optional on-device routing item).

## Remaining work (planned order)

1. **F13 reliability demo**: iPhone check, then merge (above).
2. **F10 device checklist** (from the 2026-11-07 test plan; reset with
   `python -m scripts.reset_demo_db`): Home "Your commute" card + Book;
   Siri "for Thursday" → 8:00 with reason (Console `day=` line; asks
   "Which day?" if dropped on a weekend); Preview reminder → **Book** from
   the notification; real 7 PM reminder the evening before an unbooked
   usual day; pin/unpin from card and chat; trip planner picks the 7:15 on
   Monday for "by 8:30"; schedule import says "your usual 7:15"; Claude
   Desktop `get_commute_habits`; `--no-history` fallback (all 7:30, no
   reason); widget "Book tomorrow" on a weekday; Spotlight suggestions
   after a few days.
3. **Full eval run** (36 cases, ~100 free requests, not on a demo day) and
   `--save-baseline`; current baseline is still the 33-case run.
4. **F3 leftover**: run `AIShuttle/ScheduleImportEvals/run.sh` once Apple
   Intelligence is on (on the Mac) and record the on-device model's
   numbers in AI.md.
5. **Demo runbook polish and rehearsal** (architecture slide, timings,
   fallbacks); update the original planning docs if wanted (outside the
   repo).
6. Optional: on-device Foundation Models routing (simple requests answered
   on the phone).

Not built in F10 on purpose: Smart Stack relevance (`RelevantIntentManager`)
and an in-app reminder toggle (iOS notification settings cover it).

## Known issues / caveats

- Xcode 26.4.1 build hang on the clang probe (workaround in CLAUDE.md).
- Siri on iOS 27 sometimes answers itself instead of running the intent;
  chained Siri bookings can lose the day. Use the documented phrases.
  2026-11-07: "Book my usual shuttle for Thursday" on a Saturday answered
  "Shuttles don't run on Sundays" (day dropped → tomorrow). The intent now
  asks "Which day?" when the day is missing and tomorrow is a weekend, and
  logs the received day (Console.app, category `Siri`).
- 2026-11-07: Flash-Lite once replied with the bare text
  `ValueOfget_commute_habits` after a tool call, and Siri read it out. The
  agent now treats a reply that names a tool or is a lone identifier as a
  failed attempt and moves on to the fallback model (503 if none is left).
- Eval: the judge occasionally miscounts (2026-11-05: `where-is-shuttle`
  read the pickup time as the office arrival; earlier `book-sunday-refused`).
  The two old failures passed in the 33-case run.
- Free-tier Gemini: 429s and slow responses under bursts; 3.5-flash only
  20 requests/day. Evals pace themselves (`--pause`).
- Live Activity can't update while the app is suspended unless trip mode is
  running (no APNs).
- The demo route geometry is approximate (not road-snapped).
- A simulated trip replays a *future* booking now; the Lock Screen widget
  still shows its scheduled date (user accepted this).
- `tests/manual_gemini_*.py` hit the live API (not in the pytest run).
- Apple Intelligence is **off on the Mac**, so the schedule extraction eval
  has only measured the keyword-rules baseline so far (11/15). Turning it on
  (System Settings → Apple Intelligence & Siri; free, downloads the model)
  lets `run.sh` measure the on-device model too.
- Testing on a weekend: name weekdays ("on Monday", "next week"), since
  "tomorrow" may be Sunday. Backend scripts must run from `backend/` with
  `.venv` active (`python -m scripts…` fails from `~`).
- The share extension adds a third bundle id
  (`com.yourcompany.AIShuttle.ClearPathShare`); free accounts may register
  only 10 App IDs per 7 days.

## Decision log

| Date | Decision |
|---|---|
| 2026-11-02 | Single user (no Emma); app named Clear Path kept, alternative names added |
| 2026-11-02 | Chat is secondary; OS surfaces first |
| 2026-11-02 | One booking intent with optional day (two intents confused Siri) |
| 2026-11-02 | No paid developer account → trip mode with background location instead of APNs |
| 2026-11-02 | Agent primary model gemini-3.5-flash-lite (measured), 8s deadline, fallback chain |
| 2026-11-02 | MCP 2.x SDK with own client adapter; weather server as the external example |
| 2026-11-03 | Nothing that costs money without discussing first (standing rule) |
| 2026-11-03 | No CI; Langfuse self-hosted in Docker |
| 2026-11-04 | Eval baseline saved (22/24) |
| 2026-11-05 | F3 uses a share extension: iOS 26 can't put an App Intent in the share sheet without the user building a Shortcut |
| 2026-11-05 | F3 planning is deterministic on the server, not the cloud agent: days→bookings is a rule; only typed `{date, kind}` days leave the phone, so document text can't reach Gemini or any tool |
| 2026-11-05 | F3 falls back to keyword rules when Apple Intelligence is unavailable; the same rules are the eval baseline |
| 2026-11-05 | F7 uses a deterministic trip planner exposed as tools to the one agent, not a multi-agent supervisor (user's choice): 2–3 Gemini calls per goal, no invented arrivals; goal eval 4/9 → 9/9 |
| 2026-11-05 | Eval baseline re-saved at 33 cases (32/33) |
| 2026-11-07 | F10: the learned habit drives "usual" (per weekday, with overall fallback) and is always explained; a pinned shuttle beats it; nothing is ever booked without the rider asking (user's choice) |
| 2026-11-07 | F13 outage switch is a runtime flag file (no restart); no deterministic chat fallback in this phase (user's choice) |
| 2026-11-07 | F10 surfaces: donations + evening-before reminder with Book + Home card; no Smart Stack relevance. Donations run after the rides list loads, since that sees bookings from every surface (widget extension, chat, import, MCP) |
