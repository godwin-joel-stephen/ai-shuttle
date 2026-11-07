# Demo runbook

Demo day: Tuesday or Thursday (so "tomorrow" is a weekday and Saturday is
always refused). Mac and iPhone on the same Wi-Fi.

## Before the demo (15 minutes)

1. Start Docker Desktop (app Postgres and Langfuse restart automatically).
2. Check the Mac's IP: `ipconfig getifaddr en0`. If it isn't the value of
   `BOOKING_API_BASE_URL` in Xcode, update it and reinstall the app.
3. Backend:
   ```bash
   cd ~/Projects/ai-shuttle/backend && source .venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
4. Clean state: `python -m scripts.reset_demo_db` (also adds six weeks of
   past rides, so the learned habits show: Mondays 7:15, Thursdays 8:00;
   Wed/Fri stay 7:30 so steps 1, 5 and 6 are unchanged)
5. App installed from Xcode (scheme AIShuttle). Keep
   `pkill -f "clang -v -E -dM"` handy if the build stalls.
6. On the phone: widget on the home screen, control in Control Center,
   notifications and Live Activities on for Clear Path.
7. Claude Desktop open with the clear-path MCP server running
   (Settings → Developer).
8. Langfuse open at http://localhost:3000.
9. Avoid running evals on demo day (they use the free Gemini quota).
10. Schedule samples for next week:
    `AIShuttle/ScheduleImportEvals/run.sh sample --out ~/Desktop` and
    `… sample --out ~/Desktop --injection`; AirDrop the PNGs to the phone
    (save to Photos) or show them on the Mac screen and take a photo. Book
    the Tuesday beforehand (Siri or chat) so the import has a booking to
    cancel. Check Apple Intelligence is on (Settings → Apple Intelligence &
    Siri).
11. Fallbacks ready: personal Shortcut, Type to Siri, recorded video.

## Script

1. **Siri booking** (phone locked/home): "Hey Siri, book my usual shuttle
   with Clear Path" → card → tap **Earlier**. *"No LLM call is needed when the
   request is already structured."*
2. **One tap**: Control Center button or widget **Book tomorrow** (reset or
   use another day first if already booked).
3. **Learned habit** (F10): "Hey Siri, book my usual shuttle for Monday
   with Clear Path" → "…the 7:15… That's your usual: you took it on 4 of
   your last 5 Mondays." (not the saved 7:30). Then app → **Your commute**
   card shows the next usual day not booked and why → ••• → **Preview
   reminder** → lock the phone → "Book <day>'s shuttle? … you took it
   on …" → long-press → **Book**. *"Usual is learned per weekday from real rides and always
   explained; iOS gets every booking as a donation; nothing books itself."*
4. **Schedule import**: Photos → the schedule photo → Share → **Clear Path**
   → "I'll book 2 days and cancel 1 day" (Mon/Wed booked, Tue WFH cancels
   the booking, Thu offsite / Fri leave need nothing) → **Apply**. *"The
   photo was read and understood on the iPhone by Apple's on-device model;
   only the days went to the server, and the same booking rules applied."*
   Optional F13: share the injection version → orange "Ignored 1 line that
   looked like instructions to an AI" → nothing extra proposed.
5. **Live trip**: `python -m scripts.demo_trip` → app → Where's my shuttle?
   → **Start trip mode** → lock the phone. Live Activity counts down;
   "Time to leave" arrives in ~1 minute.
6. **Delay**: `python -m scripts.demo_trip --delay 20` → notification
   offers the 7:45 → long-press → **Rebook** → "Rebooked".
7. **Siri tracking**: "Hey Siri, track my shuttle with Clear Path".
8. **Chat on purpose**: Ask Clear Path → "Why can't I book Saturday?" →
   cited Booking Policy; "Should I leave now?" → weather step "via weather
   MCP server". Goal booking (F7): "I have a meeting at 8 tomorrow, get me
   there in time" → "Planned/Booked your trip plan" step, moved to the 7:15
   (arrives 8:00); "Get me to the office by 7:30 on Wednesday" → honest "no
   shuttle gets you there; the 7:00 arrives 7:45", nothing booked. *"The
   model only turns the request into a goal; a deterministic planner picks
   the shuttle, so it can't promise an arrival that doesn't exist."*
9. **MCP**: Claude Desktop → "Book my usual shuttle for Wednesday" → refresh
   app; "Book Saturday too" → refused.
10. **Under the hood**: Langfuse trace of the last chat turn; eval baseline
   (`backend/evals/baseline.json`, or a fresh `--cases` run if quota allows).
11. **Close** with the architecture slide.

After: `python -m scripts.demo_trip --stop`.
