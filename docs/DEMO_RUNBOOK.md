# Demo runbook

Tuesday 17 November 2026, BUsoft Tech. Step by step: what to prepare, which
slide to show, what to do on the iPhone and the Mac, what to say (key
points), and which commands to run before and after each feature so the
next one works.

Three documents work together:

| Document | Use it for |
|---|---|
| This runbook | Operating the demo: setup, order, commands, state checks, recovery |
| [DEMO_SCRIPT.md](DEMO_SCRIPT.md) | The full words for every slide (the deck's speaker notes are the same text) |
| Deck: https://claude.ai/artifact/HZYoYJ5KyrqThf3Z7GCKmZ | 53 slides (52 + an appendix), Present mode; private until shared |

Slide numbers below match the deck and the script.

---

## Quick reference (print this part)

**Terminals** (all in `~/Projects/ai-shuttle/backend` with `source .venv/bin/activate`):

| Terminal | Purpose |
|---|---|
| T1 | `uvicorn app.main:app --host 0.0.0.0 --port 8000` (leave running) |
| T2 | Trip commands: `python -m scripts.demo_trip`, then `python -m scripts.demo_trip --delay 20` |
| T3 | Outage: `python -m scripts.llm_outage on` / `off`, and `curl localhost:8000/health` |

**The trip clock** (from starting `demo_trip` on slide 15; calculated from
the code, confirm in rehearsal):

- ~1 min: "Time to leave" notification.
- **Trigger the delay at about 5 min, never after 8.5 min** (after that no
  faster shuttle is catchable and there's no Rebook).
- Ask "Should I leave now?" right after Rebook (about 6–7 min): expected
  "No, leave in about 3–5 minutes". From 8.5 to 13 min it says "Yes".

**Phrases** (say them exactly):

| Slide | Phrase |
|---|---|
| 1 | "Hey Siri, book my usual shuttle with Clear Path" |
| 10 | "Hey Siri, book my usual shuttle for Monday with Clear Path" |
| 17 | "Hey Siri, track my shuttle with Clear Path" |
| 19 | "Hey Siri, ask Clear Path" → "Should I leave now?" |
| 23 | Chat: "What do I have booked?", then "Move Monday earlier" |
| 24 | Chat mic: "Why can't I book Saturday?" |
| 25 | Chat: "I have a meeting at 8 tomorrow, get me there in time", then "Get me to the office by 7:30 on Friday" |
| 26 | Claude Desktop: "Book my usual shuttle for Friday", "What's my usual Thursday?", "Book Saturday too" |
| 29 | Chat: "Why can't I book Saturday?", then "Cancel Friday"; Siri: "Hey Siri, book my usual shuttle for Friday with Clear Path" |

**If Siri doesn't run the intent:** retry once, then Type to Siri (same
phrase). Say: "That's iOS 27 Siri routing with its own model; one more for
the count."

---

## 1. The day before (Monday 16 November)

1. **Mac and phone on the venue Wi-Fi.** If you can, connect both to the
   venue network today and note the Mac's IP: `ipconfig getifaddr en0`.
   If it differs from `BOOKING_API_BASE_URL` in Xcode (Build Settings,
   project AIShuttle), update it and reinstall the app.
2. **Install a Debug build** from Xcode: scheme **AIShuttle**, run on
   "Godwin's iPhone" (⌘R). "Preview reminder" on slide 13 exists only in
   Debug builds. If the build stalls on "Discovering version info for
   clang": `pkill -f "clang -v -E -dM"`. Then stop in Xcode and launch the
   app from the Home Screen icon (the debugger slows it down).
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
| 2 | `ipconfig getifaddr en0` | Same address as `BOOKING_API_BASE_URL`; if not, update in Xcode and reinstall (Debug) |
| 3 | **T1:** `cd ~/Projects/ai-shuttle/backend && source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000` | Log shows startup without errors (the weather MCP server starts with it) |
| 4 | **T3:** `python -m scripts.llm_outage off` | `curl localhost:8000/health` → `{"status":"ok","llm":"ok"}` |
| 5 | **T2:** `python -m scripts.demo_trip --stop` | Clears any simulation left from rehearsal |
| 6 | **T2:** `python -m scripts.reset_demo_db` | "Deleted N booking(s)." and "Added 24 past ride(s) for habit learning." Must run **this week** (ride history is placed relative to the current week) |
| 7 | Restore the saved usual to the 7:30 (needed after any rehearsal that pinned the 8:00): `curl -s -X POST localhost:8000/habits/pin -H 'Content-Type: application/json' -d '{"user_id":1,"shuttle_id":3}' > /dev/null && curl -s -X POST localhost:8000/habits/pin -H 'Content-Type: application/json' -d '{"user_id":1}' > /dev/null` | Shuttle 3 is the 7:30. The second call unpins |
| 8 | Book **next Tuesday** (the schedule import cancels it): `curl -s -X POST localhost:8000/bookings -H 'Content-Type: application/json' -d '{"user_id":1,"booking_date":"2026-11-24"}'` | Reply says the 7:30 on Tuesday, November 24 |
| 9 | Check state: `curl -s "localhost:8000/bookings?user_id=1"` and `curl -s "localhost:8000/habits?user_id=1"` | Exactly one booking (24 Nov). Habits: Mon 7:15, Tue 7:30, Wed 7:30, Thu 8:00, Fri 7:30, none pinned |
| 10 | Schedule images for next week: `AIShuttle/ScheduleImportEvals/run.sh sample --out ~/Desktop` and `AIShuttle/ScheduleImportEvals/run.sh sample --out ~/Desktop --injection` (from the repo root) | Prints "week of 2026-11-23". Files: `clearpath-schedule.png` and `clearpath-schedule-injection.png` |
| 11 | AirDrop both PNGs to the iPhone and save to Photos. Delete older sample images from Photos | Both images are the two most recent in Photos |
| 12 | iPhone: open Clear Path from the icon. Home loads; **Your commute** shows "Thu isn't booked yet". Ask Clear Path → **New conversation**. If trip mode is on, tap it off. Close the app | No Live Activity on the Lock Screen; no leftover notifications (clear them) |
| 13 | Claude Desktop: open, start a new chat; Settings → Developer: `clear-path` running | Don't send a booking request |
| 14 | Browser: Langfuse logged in, Traces page open. Deck open in Present mode on the projector screen | |
| 15 | Mirror the iPhone over a cable: QuickTime → File → New Movie Recording → camera menu → the iPhone | Phone screen visible on the Mac |
| 16 | Lock the iPhone. Phone volume up (Siri replies out loud) | Ready for the cold open |

Do **not** test Siri bookings now: every booking changes the state the demo
depends on.

---

## 3. Run of show

For each step: **Before** = what must be true or run first; **Show** = what
to do; **Say** = key points (full words in the script); **After** = state
to leave behind.

### Opening

**Slide 1 · Title** (the cold open happens before it)
- Before: phone locked, mirrored; deck on slide 1 but not yet presented
  (or the projector shows the phone).
- Show: "Hey Siri, book my usual shuttle with Clear Path." Expected: "Done.
  You're on the 7:30 AM shuttle tomorrow, arriving at Office by 8:15 AM.
  That's your usual: you took it on 6 of your last 10 rides." Tap
  **Earlier** (7:15), then **Later** (back to 7:30). Then show slide 1.
- Say: booked and moved without opening an app; everything is live;
  after each step, what happened, how it works, why.
- After: tomorrow (Wed) is booked on the **7:30**. If it ended on 7:15,
  tap Later again (the delay step needs the 7:30).

**Slides 2–4 · Bridging mobile development and AI · Not a chat box · Live demo, live failures**
- Show: slides only.
- Say: mobile developer learning AI by building one real app; AI through
  the parts of iOS people already use; everything is live, count the
  failures; the three badges No AI, On-device AI, Cloud AI.

### Understanding User Intent

**Slide 5 · What just happened?** Show the five questions. Say: let's
answer them in order.

**Slide 6 · How Siri knows what my app can do** (No AI)
- Say: App Intents and App Shortcuts (9 phrases, no setup), the day enum,
  no day means tomorrow, runs without opening the app, the snippet card's
  Earlier/Later are intents too, no LLM: structured requests skip the AI.

**Slide 7 · From the phone to the backend**
- Say: HTTP over Wi-Fi to FastAPI on the Mac; Postgres + pgvector in
  Docker; Langfuse self-hosted; three app targets; on-device models; only
  Gemini and a weather API in the cloud; zero spend.

**Slide 8 · One booking service for every surface** (No AI)
- Say: five shuttles, five rules in order, asking twice returns the
  existing booking; facts deterministic; rules in one place; six weeks of
  past rides in the database.

### Learning User Habits

**Slide 9 · What does "my usual" mean?** (No AI)
- Show: open the app → Home → **Your commute**: "Thu isn't booked yet",
  8:00 → 8:45, "You took it on 4 of your last 5 Thursdays". Expand **Your
  usual week**. **Don't tap Book** (the reminder books Thursday).
- Say: HabitService order (pin, last 5 that weekday, last 10 overall,
  saved default), 3+ rides and a majority, 8 weeks; Wednesday used the
  overall pattern (6 of last 10); counting, so it can always say why.

**Slide 10 · The explanation travels with the booking** (No AI)
- Show: lock or leave the app, then "Hey Siri, book my usual shuttle for
  Monday with Clear Path." Expected: "Done. You're on the 7:15 AM shuttle
  on Monday, arriving at Office by 8:00 AM. That's your usual: you took it
  on 4 of your last 5 Mondays."
- Say: same intent with a day; the reason comes back with the booking;
  bookings are donated to iOS when the app loads rides.
- After: next Monday 7:15 booked.

**Slide 11 · You stay in control** (No AI)
- Show: app → Your commute → menu → **Always use the 8:00 AM** (pin
  appears) → menu → **Learn from my rides again**.
- Say: visible, explainable, overridable; a pin changes no bookings.
- After: **must be unpinned** (while pinned every day's usual is 8:00).
  Don't say "the saved 7:30" from here on (pinning made the 8:00 the saved
  default; section 2 step 7 restores it next time).

### One Backend, Multiple Entry Points

**Slide 12 · One backend, multiple iOS entry points** (No AI)
- Show: Home Screen widget (tomorrow's ride, no Book tomorrow button);
  Lock Screen widget; Control Center → **Book Usual Shuttle** (or the Action
  button). Expected: notification "Already booked".
- Say: WidgetKit and a Control Widget run an intent in the widget
  extension; the server's duplicate check answered; same backend, same
  rules.
- After: nothing changes.

### Proactive Mobile Experiences

**Slide 13 · A reminder that suggests, never books** (No AI)
- Show: app → Your commute → menu → **Preview reminder** → lock the phone →
  within ~5 s "Book Thursday's shuttle?" → long-press → **Book** → "Shuttle
  booked".
- Say: normally 7 PM the evening before an unbooked usual day; the action
  runs in the background; booking elsewhere withdraws it; suggests, never
  books.
- After: this Thursday 8:00 booked.

### Handling Schedule Changes

**Slide 14 · When the week doesn't follow the routine** (On-device AI)
- Show: Photos → `clearpath-schedule.png` → Share → **Clear Path**. Review:
  Monday **keep**, Tuesday WFH **cancel**, Wednesday **book**, Thursday
  offsite and Friday leave **nothing needed**. Toggle one row off and on.
  Point at "Read on this iPhone with Apple Intelligence" and "Text read
  from your document". Tap **Apply 2 Changes**.
- Say: Vision OCR → safety step → on-device Foundation Model with guided
  generation (weekday, date, kind only) → code validation → server plans
  with the same rules; document never leaves the phone; PDFs via Home.
- After: next Tuesday cancelled, next Wednesday booked.
- If the label says "text rules": Apple Intelligence wasn't available;
  explain the fallback and continue.

### Real-Time Assistance (the trip clock starts here)

**Slide 15 · Where's my shuttle?** (No AI)
- Before: tomorrow is booked on the 7:30 (from slide 1).
- Show: **T2:** `python -m scripts.demo_trip` (**note the time: r = 0**).
  Phone: app → **Where's my shuttle**: map, bus, "Simulated" tag, walk
  advice. Go straight to slide 16.
- Say: simulated replay of tomorrow's 7:30 at 2×, illustrative route,
  MapKit polling every 5 s, walk fixed at 4 minutes in the demo.

**Slide 16 · Trip mode and the Live Activity** (No AI)
- Show: tap **Start trip mode** → lock the phone → Live Activity on the
  Lock Screen and in the Dynamic Island.
- Say: push needs a paid account, so background location keeps the app
  alive; every 15 s it updates the Live Activity; location every 50 m or
  2 min.

**Slide 17 · Time to leave, and asking Siri** (No AI)
- Show: at ~1 min the "Time to leave" notification. Then (by ~4 min) "Hey
  Siri, track my shuttle with Clear Path."
- Say: walk + 5-minute buffer; Live Activity intent; the "Where's my
  shuttle" lesson.
- Watch the clock: if Siri fails, Type to Siri, but don't let it push the
  delay past ~7 min.

**Slide 18 · A delay, and a better shuttle** (No AI)
- Show: at **r ≈ 5** (never after 8.5): **T2:** `python -m scripts.demo_trip
  --delay 20`. Within ~15 s: "20 min late", orange bar, notification offering
  the 7:45 → long-press → **Rebook** → "Rebooked".
- Say: trip planner picks the catchable shuttle that arrives soonest
  (delayed 7:30 arrives 8:35, the 7:45 arrives 8:30); no AI, arithmetic.
- After: tomorrow is on the **7:45**; the simulation follows it. Go
  straight to slide 19.
- If there's no Rebook: the delay came too late; say it's correct
  behaviour, and slide 19 answers for the 7:30.

### When AI Needs to Think

**Slide 19 · A question, not a command** (Cloud AI)
- Before: within a few minutes of the Rebook (ideally r ≈ 6–7).
- Show: "Hey Siri, ask Clear Path" → "Should I leave now?" Expected: "No",
  leave in about 3–5 minutes (or "Yes" if r is 8.5–13), maybe with an
  umbrella tip.
- Say: a question needing several facts; the first interaction that needs
  cloud-based reasoning; the on-device assistant declined, so the cloud
  agent answered.
- If slow: free tier; 8 s per attempt, then fallback; count it.

**Slides 20–21 · How the agent works · Calculations in code, data from tools** (Cloud AI)
- Say: LangGraph loop (up to 12 steps), 12 tools, application facts only
  from tools, Gemini 3.5 Flash-Lite → retry → 3.1 Flash-Lite with 8 s
  deadlines; "leave now" computed in code; weather from my MCP server.

**Slide 22 · One conversation across Siri and the app** (Cloud AI)
- Show: app → **Ask Clear Path**: the Siri question is there with
  "Checked the weather · via weather MCP server".
- Say: shared conversation id (30 minutes); LangGraph checkpoints in
  Postgres; action rows, sources, suggestions, new-conversation button.

**Slide 23 · Not every message needs the cloud** (On-device AI)
- Show: type "What do I have booked?" → **On device · Apple Intelligence**
  label. Then "Move Monday earlier" → next Monday 7:15 → 7:00.
- Say: rules gate → on-device model (3 s) → must agree → same endpoints;
  turn saved to the conversation.
- After: next Monday on the 7:00.

**Slide 24 · Answers with sources** (On-device AI + Cloud AI)
- Show: tap the mic → "Why can't I book Saturday?" → tap stop. Expected:
  the rule and a cited Booking Policy.
- Say: on-device speech; eligibility tool; RAG over 16 sections, local
  embeddings in pgvector; below 0.60 dropped, 0.60–0.70 used but not
  cited, 0.70+ citable.
- If the mic isn't available, type it.

**Slide 25 · Goals instead of times** (Cloud AI + No AI)
- Show: "I have a meeting at 8 tomorrow, get me there in time" → "Booked
  your trip plan": tomorrow 7:45 → 7:15 (arrives 8:00). Then "Get me to
  the office by 7:30 on Friday" → no shuttle gets there; the 7:00 arrives
  7:45; nothing booked.
- Say: the model reads, the deterministic planner decides; 4/9 → 9/9.
- After: tomorrow on the 7:15; Friday still unbooked.

### Connecting External AI Systems

**Slide 26 · Booking from Claude Desktop** (Cloud AI; Clear Path side No AI)
- Before: Friday is not booked.
- Show: Claude Desktop: "Book my usual shuttle for Friday" → allow the tool
  → booked → refresh the app on the phone: Friday is there. "What's my
  usual Thursday?" → 8:00 with its reason. "Book Saturday too" → refused.
- Say: MCP in the other direction; 13 tools, same services and rules;
  annotations (cancel is destructive).
- After: this Friday 7:30 booked (the outage step cancels it).

### Engineering for Failure

**Slide 27 · Designing for failure.** Say: two failures on purpose; rule
five.

**Slide 28 · A document with hidden instructions** (On-device AI)
- Show: Photos → `clearpath-schedule-injection.png` → Share → Clear Path →
  orange "Ignored 1 line that looked like instructions to an AI".
  **Close without applying.**
- Say: five layers of defence; the honest limit.
- After: nothing changed.

**Slide 29 · The cloud AI goes down** (Cloud AI (unavailable) + No AI + On-device AI)
- Show: **T3:** `python -m scripts.llm_outage on`; optional `curl
  localhost:8000/health` → `"llm":"outage"`. Chat: "Why can't I book
  Saturday?" → the unavailable message. Chat: "Cancel Friday" → On device,
  Friday cancelled. Siri: "Hey Siri, book my usual shuttle for Friday with
  Clear Path" → booked. Optionally press the Control Center control.
- Say: honest 503 after the real fallback chain; on-device and structured
  paths keep working; the AI is an enhancement, not a single point of
  failure.
- After: Friday booked again; **outage still on** until slide 30.

**Slide 30 · Tracing every turn**
- Show: Langfuse → the failed turn (ERROR, each attempt) → a normal turn
  (model calls, tool spans) → an on-device turn. Then **T3:** `python -m
  scripts.llm_outage off`, and ask the chat any question to show it's
  back.
- Say: self-hosted tracing; never hide a real change ("I made changes to
  your bookings…").
- After: **outage off**, `/health` shows `"llm":"ok"`.

**Slide 31 · If something failed earlier** (optional): only if something
failed naturally; otherwise skip.

### Testing AI Behaviour, Limitations, Architecture

**Slides 32–36** (no live steps): how I know it works; three layers of
checking; how an evaluation works; measured results (36-scenario baseline, the
three failures and their fixes); four bugs evaluations caught, each tied to an
earlier slide.

**Slides 37–38**: ask the room for the failure count; Siri limits; model
and platform limits.

**Slides 39–41**: one backend, many surfaces; where the AI runs; the five
design rules recap.

### From Prototype to Production

**Slides 42–52** (no live steps): lessons; scaling up for the real world;
users and security; platform and scale; mobile; AI quality and cost; cost
estimate; roadmap; what this means for our projects; closing line;
questions. Slide 53 (appendix glossary) only if asked.

---

## 4. Recovery

| Symptom | Do | Say |
|---|---|---|
| Siri answers itself / "Clear Path doesn't support that" | Retry once, then Type to Siri | iOS 27 Siri routes with its own model; count it |
| "I couldn't reach Clear Path" | Check T1 is running; `ipconfig getifaddr en0` matches the app; both on the same Wi-Fi | Every surface reports it plainly |
| Chat slow / "Working on it…" for long | Wait up to ~25 s (three 8 s attempts) | Free tier; deadlines and fallbacks |
| Chat says unavailable when it shouldn't | **T3:** `python -m scripts.llm_outage` (shows the state); `off` if on | |
| No "On device" label | Continue; the cloud answered | The model must agree with the rules gate |
| Schedule import says "text rules" | Continue | Apple Intelligence unavailable; keyword fallback |
| No Live Activity | Settings → Clear Path → Live Activities on; restart trip mode | |
| No delay notification | Check trip mode is on (Where's my shuttle shows "Trip mode on"); wait 15 s | |
| No Rebook button | Continue to slide 19 | Too late for a faster shuttle: correct behaviour |
| Claude Desktop shows no tools | Settings → Developer → restart `clear-path`; Postgres must be running | |
| Preview reminder missing | It's Debug-only; book Thursday from the card's **Book** button instead | |
| Wrong state discovered mid-demo | Carry on and explain; don't reset live | |

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

Rehearse on a **Tuesday** if you can (for example 10 November): the whole
booking chain, the expected Siri replies and "tomorrow = Wednesday" assume
it. Use that week's next-Tuesday date in step 8 and regenerate the schedule
images in the same week. On another weekday the steps still run, but
tomorrow's usual, the replies and the delay alternative change (on a
Friday or Saturday, tomorrow is a weekend and the Control Center step
fails).
