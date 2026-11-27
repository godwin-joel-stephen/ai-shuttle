# Demo runbook

Thursday 3 December 2026, BUsoft Tech. Tomorrow is Friday, and a weekday
name said on the day means next week's ("Monday" = 7 December,
"Thursday" = 10 December). Step by step: what to prepare, which slide to
show, what to do on the iPhone and the Mac, what to say (key points), and
which commands to run before and after each step so the next one works.

Three documents work together:

| Document | Use it for |
|---|---|
| This runbook | Operating the demo: setup, the 24 steps, commands, state checks, recovery |
| [DEMO_SCRIPT.md](DEMO_SCRIPT.md) | The full words for every slide (the deck's speaker notes are the same text) |
| Deck: https://claude.ai/artifact/HZYoYJ5KyrqThf3Z7GCKmZ | 27 slides, Present mode; private until shared |

Step numbers in the run of show are the 24 demo steps; each names its
slide. About 50 minutes plus questions.

---

## Quick reference (print this part)

**Terminals** (all in `~/Projects/ai-shuttle/backend` with `source .venv/bin/activate`):

| Terminal | Purpose |
|---|---|
| T1 | `python -m scripts.serve` (leave running; IPv4 + IPv6) |
| T2 | Trip commands: `python -m scripts.demo_trip`, then `python -m scripts.demo_trip --delay 20` |
| T3 | Outage: `python -m scripts.llm_outage on` / `off`, and `curl localhost:8000/health` |

**The trip clock** (from starting `demo_trip` in step 9; calculated from
the code, confirm in rehearsal):

- ~1 min: "Time to leave" notification.
- By ~4 min: "Hey Siri, track my shuttle with Clear Path".
- **Trigger the delay at about 5 min, never after 8.5 min** (after that no
  faster shuttle is catchable and there's no Rebook).
- Ask "Should I leave now?" right after Rebook (about 6–7 min): expected
  "No, leave in about 3–5 minutes". From 8.5 to 13 min it says "Yes".

**Phrases** (say them exactly):

| Step | Slide | Phrase |
|---|---|---|
| 1 | 1 | "Hey Siri, book my usual shuttle with Clear Path" |
| 4 | 7 | "Hey Siri, book my usual shuttle for Monday with Clear Path" |
| 9 | 10 | "Hey Siri, track my shuttle with Clear Path" |
| 10 | 12 | "Hey Siri, ask Clear Path" → "Should I leave now?" |
| 11 | 13 | Chat: "What do I have booked?", then "Move Monday earlier" |
| 12 | 14 | Chat mic: "Why can't I book Saturday?" |
| 13 | 15 | Chat: "I have a meeting at 8 tomorrow, get me there in time", then "Get me to the office by 7:30 on Tuesday" |
| 14 | 16 | Claude Desktop: "My offsite next Thursday was cancelled. Book my usual shuttle for Thursday 10 December", "What's my usual Monday?", "Book Saturday too" |
| 15 | 17 | Chat: "Why can't I book Saturday?", then "Cancel Thursday"; Siri: "Hey Siri, book my usual shuttle for Thursday with Clear Path" |
| 20 | 22 | redBus in the background: "Hey Siri, where's my bus pickup point?"; then "Hey Siri, track my shuttle" (no app name, on purpose) |

**If Siri doesn't run the intent:** retry once, then Type to Siri (same
phrase). Say: "That's iOS 27 Siri routing with its own model; one more for
the count."

---

## 1. The day before (Wednesday 2 December)

1. **Mac and phone on the venue Wi-Fi.** If you can, connect both to the
   venue network (or the mobile hotspot) today and open
   `http://BUSOFT-MB30-7.local:8000/health` in Safari on the phone with
   the backend running. The app uses that name, so no IP to update.
2. **Install a Debug build** from Xcode (a build signed with the free
   account stops opening after 7 days, so install it today, not earlier):
   scheme **AIShuttle**, run on "Godwin's iPhone" (⌘R). "Preview reminder"
   in step 7 exists only in Debug builds. If the build stalls on
   "Discovering version info for clang": `pkill -f "clang -v -E -dM"`.
   Then stop in Xcode and launch the app from the Home Screen icon (the
   debugger slows it down).
3. **Phone setup** (once):
   - Settings → Apple Intelligence & Siri: Apple Intelligence **on** and
     downloaded; Siri on, "Hey Siri" on.
   - Settings → Notifications → Clear Path: allowed, Time Sensitive on.
   - Settings → Clear Path: Live Activities on, Location "While Using".
   - Home Screen: Clear Path widget (small or medium). Lock Screen:
     Clear Path rectangular widget.
   - Control Center: add the "Book Usual Shuttle" control. Action button:
     assign the same control (Settings → Action Button → Controls).
   - Focus / Do Not Disturb off; Low Power Mode off (it limits background
     location for trip mode).
   - redBus (step 20): signed in, with an upcoming trip whose boarding
     point shows in the app. Try "Hey Siri, where's my bus pickup point?"
     once today with redBus in the background; it should answer without
     the app name. If it doesn't, the step is talk-only.
4. **Claude Desktop:** Settings → Developer shows the `clear-path` MCP
   server running (config in [MCP.md](MCP.md)). Don't book anything in it
   today.
5. **Langfuse:** log in at http://localhost:3000 (the login is printed by
   `python3 observability/setup_env.py`, which changes nothing if already
   set up). Keep the browser session.
6. **Do not run evals today or tomorrow** (they share the free Gemini quota).
7. **Rehearse once** with section 3 below, timing the trip clock, then
   reset with section 5.

---

## 2. Demo morning (start 60 minutes before)

Run these in order. Each has a check; don't move on until it passes.

| # | Do | Check |
|---|---|---|
| 1 | Start **Docker Desktop**. If the containers didn't start: `docker compose up -d` in the repo root, and `docker compose up -d` in `observability/` | `docker ps` lists `ai-shuttle-postgres` and the Langfuse containers |
| 2 | `scutil --get LocalHostName` | `BUSOFT-MB30-7` (the app's `BOOKING_API_BASE_URL` is `http://BUSOFT-MB30-7.local:8000`); if the Mac was renamed, update in Xcode and reinstall (Debug) |
| 3 | **T1:** `cd ~/Projects/ai-shuttle/backend && source .venv/bin/activate && python -m scripts.serve` | Log shows startup without errors (the weather MCP server starts with it) |
| 4 | **T3:** `python -m scripts.llm_outage off` | `curl localhost:8000/health` → `{"status":"ok","llm":"ok"}` |
| 5 | **T2:** `python -m scripts.demo_trip --stop` | Clears any simulation left from rehearsal |
| 6 | **T2:** `python -m scripts.reset_demo_db` | "Deleted N booking(s)." and "Added 24 past ride(s) for habit learning." Must run **this week** (ride history is placed relative to the current week; a run at the 26 November rehearsal is not enough) |
| 7 | Restore the saved usual to the 7:30 (needed after any rehearsal that pinned the 8:00): `curl -s -X POST localhost:8000/habits/pin -H 'Content-Type: application/json' -d '{"user_id":1,"shuttle_id":3}' > /dev/null && curl -s -X POST localhost:8000/habits/pin -H 'Content-Type: application/json' -d '{"user_id":1}' > /dev/null` | Shuttle 3 is the 7:30. The second call unpins |
| 8 | Book **next Tuesday** (the schedule import cancels it): `curl -s -X POST localhost:8000/bookings -H 'Content-Type: application/json' -d '{"user_id":1,"booking_date":"2026-12-08"}'` | Reply says the 7:30 on Tuesday, December 8 |
| 9 | Check state: `curl -s "localhost:8000/bookings?user_id=1"` and `curl -s "localhost:8000/habits?user_id=1"` | Exactly one booking (8 Dec). Habits: Mon 7:15, Tue 7:30, Wed 7:30, Thu 8:00, Fri 7:30, none pinned |
| 10 | Schedule image for next week: `AIShuttle/ScheduleImportEvals/run.sh sample --out ~/Desktop` (from the repo root) | Prints "week of 2026-12-07". File: `clearpath-schedule.png` |
| 11 | AirDrop the PNG to the iPhone and save it to Photos. Delete older sample images from Photos | It's the most recent image in Photos |
| 12 | iPhone: open Clear Path from the icon. Home loads; **Your commute** shows "Fri isn't booked yet" (it changes to Monday once step 1 books tomorrow). Ask Clear Path → **New conversation**. If trip mode is on, tap it off. Close the app | No Live Activity on the Lock Screen; no leftover notifications (clear them) |
| 13 | Claude Desktop: open, start a new chat; Settings → Developer: `clear-path` running | Don't send a booking request |
| 14 | Browser: Langfuse logged in, Traces page open. Deck open in Present mode on the projector screen | |
| 15 | Mirror the iPhone over a cable: QuickTime → File → New Movie Recording → camera menu → the iPhone | Phone screen visible on the Mac |
| 16 | Lock the iPhone. Phone volume up (Siri replies out loud) | Ready for the cold open |

Do **not** test Siri bookings now: every booking changes the state the demo
depends on.

---

## 3. Run of show: the 24 steps

For each step: **Before** = what must be true or run first; **Show** = what
to do; **Say** = key points (full words in the script); **After** = state
to leave behind.

### Step 1 · Siri books tomorrow (slide 1, before showing it) · No AI
- Before: phone locked, mirrored; deck on slide 1 but not yet presented.
- Show: "Hey Siri, book my usual shuttle with Clear Path." Expected: "Done.
  You're on the 7:30 AM shuttle tomorrow, arriving at Office by 8:15 AM.
  That's your usual: you took it on each of your last 5 Fridays." Tap
  **Earlier** (7:15), then **Later** (back to 7:30). Then show slide 1.
- Say: booked and moved without opening an app; everything is live.
- After: tomorrow (Fri) is on the **7:30**. If it ended on 7:15, tap Later
  again (the delay step needs the 7:30).

### Step 2 · Intro, AI and iOS terms, and what just happened (slides 2–5) · No AI
- Show: slides only.
- Say: mobile developer learning AI by building one real app; AI through
  the parts of iOS people already use; count the failures; the three
  badges. Then the eight AI terms and the eight iOS terms (one line
  each). Then: App Intents and App Shortcuts, the day enum (no day means
  tomorrow), HTTP to the Mac, one BookingService with five rules, no LLM
  because the request was already structured.

### Step 3 · Your commute card (slide 6) · No AI
- Show: app → Home → **Your commute**: "Mon isn't booked yet", 7:15 →
  8:00, "You took it on 4 of your last 5 Mondays". Expand **Your usual
  week**. **Don't tap Book.**
- Say: HabitService order (pin, last 5 that weekday, last 10 overall,
  saved default), 3+ rides and a majority, 8 weeks; counting, so it can
  always say why.

### Step 4 · Siri books Monday, with its reason (slide 7) · No AI
- Show: lock or leave the app, then "Hey Siri, book my usual shuttle for
  Monday with Clear Path." Expected: "Done. You're on the 7:15 AM shuttle
  on Monday, arriving at Office by 8:00 AM. That's your usual: you took it
  on 4 of your last 5 Mondays."
- After: next Monday 7:15 booked.

### Step 5 · Pin and unpin (slide 7) · No AI
- Show: app → Your commute → menu → **Always use the 8:00 AM** (pin
  appears) → menu → **Learn from my rides again**.
- Say: visible, explainable, overridable; a pin changes no bookings.
- After: **must be unpinned** (while pinned every day's usual is 8:00).
  Don't say "the saved 7:30" from here on.

### Step 6 · Widgets and Control Center (slide 8) · No AI
- Show: Home Screen widget (tomorrow's ride, no Book tomorrow button);
  Lock Screen widget; Control Center → **Book Usual Shuttle** (or the
  Action button). Expected: notification "Already booked".
- Say: WidgetKit and a Control Widget run an intent in the widget
  extension; the server's duplicate check answered.
- After: nothing changes.

### Step 7 · Reminder notification → Book (slide 8) · No AI
- Show: app → Your commute → menu → **Preview reminder** → lock the phone
  → within ~5 s "Book Thursday's shuttle?" (next Thursday, 10 Dec) →
  long-press → **Book** → "Shuttle booked".
- Say: normally 7 PM the evening before an unbooked usual day; the action
  runs in the background; suggests, never books.
- After: next Thursday (10 Dec) 8:00 booked.

### Step 8 · Schedule image import (slide 9) · On-device AI
- Show: Photos → `clearpath-schedule.png` → Share → **Clear Path**. Review:
  Monday **keep**, Tuesday WFH **cancel**, Wednesday **book**, Thursday
  offsite **cancel** (the reminder's booking from step 7: point it out),
  Friday leave **nothing needed**. Toggle one row off and on. Point at
  "Read on this iPhone with Apple Intelligence" and "Text read from your
  document". Tap **Apply 3 Changes**.
- Say: Vision OCR → on-device Foundation Model with guided generation
  (weekday, date, kind only) → code validation → server plans with the
  same rules; the document never leaves the phone; instruction-like lines
  are dropped (one sentence, no demo).
- After: next Tuesday and Thursday cancelled, next Wednesday booked.
- If the label says "text rules": Apple Intelligence wasn't available;
  explain the fallback and continue.

### Step 9 · Live trip: map, trip mode, Live Activity, time to leave, Siri track (slide 10) · No AI
- Before: tomorrow is booked on the 7:30 (from step 1).
- Show:
  1. **T2:** `python -m scripts.demo_trip` (**note the time: r = 0**).
  2. App → **Where's my shuttle**: map, bus, "Simulated" tag, walk advice.
  3. Tap **Start trip mode** → lock the phone → Live Activity on the Lock
     Screen and in the Dynamic Island.
  4. At ~1 min: the "Time to leave" notification.
  5. By ~4 min: "Hey Siri, track my shuttle with Clear Path."
- Say: simulated replay of tomorrow's 7:30 at 2×; no push without a paid
  account, so background location keeps the app updating every 15 s; walk
  + 5-minute buffer; "Track", not "Where's", because Siri intercepted it.
- Watch the clock: if Siri fails, Type to Siri, but don't let it push the
  delay past ~7 min.

### Step 10 · Delay → Rebook (slide 11) · No AI
- Show: at **r ≈ 5** (never after 8.5): **T2:** `python -m scripts.demo_trip
  --delay 20`. Within ~15 s: "20 min late", orange bar, notification
  offering the 7:45 → long-press → **Rebook** → "Rebooked".
- Say: the trip planner picks the catchable shuttle that arrives soonest
  (delayed 7:30 arrives 8:35, the 7:45 arrives 8:30); arithmetic, no AI.
- After: tomorrow is on the **7:45**; the simulation follows it. Go
  straight to step 11.
- If there's no Rebook: the delay came too late; say it's correct
  behaviour, and step 11 answers for the 7:30.
- (Trip mode stays on; stop it after the talk, section 5.)

### Step 11 · "Should I leave now?" with MCP weather (slide 12) · Cloud AI
- Before: within a few minutes of the Rebook (ideally r ≈ 6–7).
- Show: "Hey Siri, ask Clear Path" → "Should I leave now?" Expected: "No",
  leave in about 3–5 minutes (or "Yes" if r is 8.5–13), plus the umbrella
  or no-umbrella sentence.
- Say: a question needing several facts; LangGraph loop with 12 tools;
  "leave now" computed in code; weather from my MCP server; Gemini 3.5
  Flash-Lite → retry → 3.1 Flash-Lite, 8 s each.
- If slow: free tier; 8 s per attempt, then fallback; count it.

### Step 12 · Chat: shared conversation, then on device (slide 13) · Cloud AI + On-device AI
- Show: app → **Ask Clear Path**: the Siri question is there with "Checked
  the weather · via weather MCP server". Type "What do I have booked?" →
  **On device · Apple Intelligence**. Then "Move Monday earlier" → next
  Monday 7:15 → 7:00.
- Say: shared conversation id (30 minutes), checkpoints in Postgres; rules
  gate → on-device model (3 s) → must agree → same endpoints.
- After: next Monday on the 7:00.

### Step 13 · "Why can't I book Saturday?" by voice, RAG (slide 14) · On-device AI + Cloud AI
- Show: tap the mic → "Why can't I book Saturday?" → tap stop. Expected:
  the rule and a cited Booking Policy.
- Say: on-device speech; eligibility tool; RAG over 16 sections, local
  embeddings in pgvector; below 0.60 dropped, 0.70+ citable.
- If the mic isn't available, type it.

### Step 14 · Goal planning (slide 15) · Cloud AI + No AI
- Show: "I have a meeting at 8 tomorrow, get me there in time" → "Booked
  your trip plan": tomorrow 7:45 → 7:15 (arrives 8:00). Then "Get me to the
  office by 7:30 on Tuesday" (next Tuesday, unbooked since the import) →
  no shuttle gets there; the 7:00 arrives 7:45; nothing booked.
- Say: the model reads, the deterministic planner decides; 4/9 → 9/9.
- After: tomorrow on the 7:15; next Tuesday still unbooked.

### Step 15 · Claude Desktop through MCP (slide 16) · Cloud AI; Clear Path side No AI
- Before: next Thursday (10 Dec) is not booked (the import cancelled it).
- Show: Claude Desktop: "My offsite next Thursday was cancelled. Book my
  usual shuttle for Thursday 10 December" → allow the tool → the 8:00 with
  its reason → refresh the app on the phone: Thursday is there. "What's my
  usual Monday?" → 7:15 with its reason. "Book Saturday too" → refused.
  Name the date: "Thursday" alone, said on a Thursday, could mean today.
- Say: MCP in the other direction; 13 tools, same services and rules;
  annotations (cancel is destructive).
- After: next Thursday 8:00 booked (the outage step cancels it).

### Step 16 · The cloud AI goes down (slide 17) · Cloud AI (unavailable) + On-device AI + No AI
- Show: **T3:** `python -m scripts.llm_outage on`; optional `curl
  localhost:8000/health` → `"llm":"outage"`. Chat: "Why can't I book
  Saturday?" → the unavailable message. Chat: "Cancel Thursday" → On
  device, next Thursday cancelled (**not Friday**: that's tomorrow's trip).
  Siri: "Hey Siri, book my usual shuttle for Thursday with Clear Path" →
  the 8:00 on Thursday, booked. Optionally press the Control Center
  control ("Already booked").
- Say: honest 503 after the real fallback chain; on-device and structured
  paths keep working; the AI is an enhancement, not a single point of
  failure.
- After: next Thursday booked again; **outage still on** until step 17.

### Step 17 · Langfuse (slide 18)
- Show: Langfuse → the failed turn (ERROR, each attempt) → a normal turn
  (model calls, tool spans) → an on-device turn. Then **T3:** `python -m
  scripts.llm_outage off`, and ask the chat any question to show it's
  back.
- Say: self-hosted tracing; never hide a real change ("I made changes to
  your bookings…").
- After: **outage off**, `/health` shows `"llm":"ok"`.

### Step 18 · Evaluations (slides 19–20)
- Show: slides only.
- Say: three layers (≈150 backend tests, 76 Swift + 2 UI tests, 36 agent
  scenarios + 15 extraction documents); setup → messages → hard checks →
  judge; baseline 33/36, judge 4.67/5; four bugs caught, each tied to a
  slide (13, 5, 12, 10).

### Step 19 · Why not reliable (slide 21)
- Show: slide only. Ask the room for the failure count and recap each in
  one line (natural-failure explanations are in the slide's notes).
- Say: Siri routes with its own model ("Clear Footpath", dropped day,
  "Where's my shuttle"); on-device AI not on every iPhone; no push without
  a paid account; free-tier latency; making AI trustworthy is most of the
  work.

### Step 20 · Siri is catching up: redBus on iOS 27 (slide 22) · No AI (Clear Path)
- Do: open redBus on the trip, swipe home. "Hey Siri, where's my bus
  pickup point?" → Siri answers from redBus, no app name. Then "Hey Siri,
  track my shuttle" (no app name) → Siri asks Wallet or Clear Path, or
  answers itself. Don't pick an app; dismiss Siri.
- Say: iOS 27 rebuilt Siri; intent schemas (`@AppIntent(schema:)`),
  indexed entities (`IndexedEntity`), screen awareness
  (`.appEntityIdentifier`); Clear Path is on the iOS 26.4 SDK, so none of
  this yet; the app name is becoming optional.
- If redBus doesn't answer: count it, explain from the slide.

### Step 21 · More from iOS 27 (slide 23)
- Show: slide only.
- Say: Private Cloud Compute for developers (large server model, no API
  keys, no cost under 2M downloads, eligibility terms differ); Foundation
  Models upgrade (better tool calling, 8K context, image input, OCR and
  barcode tools, one LanguageModel protocol, Evaluations framework); App
  Intents beyond Siri (RelevantEntities, LongRunningIntent,
  AppIntentsTesting, Siri acting on notifications); all need Xcode 27,
  after the demo.

### Step 22 · Architecture recap (slide 24)
- Show: slide only.
- Say: iPhone surfaces and on-device models → Wi-Fi → FastAPI with two
  paths (REST / LangGraph → Gemini) → services → Docker (Postgres 17 +
  pgvector; Langfuse's six containers); MCP in and out; evals; ₹0; the five
  design rules.

### Step 23 · Prototype → full scale (slide 25)
- Show: slide only.
- Say: four areas (users and security, platform, mobile, AI quality and
  cost), the ~$8/day estimate, and the areas to focus on next (iOS 27
  Siri first).

### Step 24 · Our projects, close and questions (slides 26–27)
- Show: slide 26, then the thank-you slide 27; stay on 27 for questions.
- Say: the four-step pattern for any client app; the closing line;
  questions (prepared answers in the script, including prompt injection).

---

## 4. Recovery

| Symptom | Do | Say |
|---|---|---|
| Siri answers itself / "Clear Path doesn't support that" | Retry once, then Type to Siri | iOS 27 Siri routes with its own model; count it |
| "I couldn't reach Clear Path" | Check T1 is running (`scripts.serve`, not `uvicorn --host 0.0.0.0`); phone Safari opens `http://BUSOFT-MB30-7.local:8000/health`; both on the same network | Every surface reports it plainly |
| Chat slow / "Working on it…" for long | Wait up to ~25 s (three 8 s attempts) | Free tier; deadlines and fallbacks |
| Chat says unavailable when it shouldn't | **T3:** `python -m scripts.llm_outage` (shows the state); `off` if on | |
| No "On device" label | Continue; the cloud answered | The model must agree with the rules gate |
| Schedule import says "text rules" | Continue | Apple Intelligence unavailable; keyword fallback |
| No Live Activity | Settings → Clear Path → Live Activities on; restart trip mode | |
| No delay notification | Check trip mode is on (Where's my shuttle shows "Trip mode on"); wait 15 s | |
| No Rebook button | Continue to step 11 | Too late for a faster shuttle: correct behaviour |
| Claude Desktop shows no tools | Settings → Developer → restart `clear-path`; Postgres must be running | |
| Preview reminder missing | It's Debug-only; book next Thursday from the card's **Book** button instead | |
| Wrong state discovered mid-demo | Carry on and explain; don't reset live | |

Something that failed by itself is explained on slide 21 (the failure
count), not on a separate slide.

---

## 5. After the demo, or between rehearsals

```bash
cd ~/Projects/ai-shuttle/backend && source .venv/bin/activate
python -m scripts.demo_trip --stop
python -m scripts.llm_outage off
```

On the phone: Where's my shuttle → tap trip mode off; dismiss the Live
Activity; clear notifications.

To rehearse again, repeat section 2 from step 4 (outage off, stop the trip,
reset, restore the saved 7:30, book next Tuesday, check state).

Rehearse on a **Thursday** if you can (26 November is the only one
before the demo): the whole booking chain, the expected Siri replies and
"tomorrow = Friday" assume it. For that rehearsal use 2026-12-01 in step
8 (it prints "Tuesday, December 1") and expect "week of 2026-11-30" in
step 10; run `reset_demo_db` again in the demo week. On another weekday
the steps still run, but tomorrow's usual, the replies, the day the card
suggests and the delay alternative change (on a Friday or Saturday,
tomorrow is a weekend and the Control Center step fails).
