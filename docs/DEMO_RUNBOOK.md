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
4. Clean state: `python -m scripts.reset_demo_db`
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
3. **Schedule import**: Photos → the schedule photo → Share → **Clear Path**
   → "I'll book 2 days and cancel 1 day" (Mon/Wed booked, Tue WFH cancels
   the booking, Thu offsite / Fri leave need nothing) → **Apply**. *"The
   photo was read and understood on the iPhone by Apple's on-device model;
   only the days went to the server, and the same booking rules applied."*
   Optional F13: share the injection version → orange "Ignored 1 line that
   looked like instructions to an AI" → nothing extra proposed.
4. **Live trip**: `python -m scripts.demo_trip` → app → Where's my shuttle?
   → **Start trip mode** → lock the phone. Live Activity counts down;
   "Time to leave" arrives in ~1 minute.
5. **Delay**: `python -m scripts.demo_trip --delay 20` → notification
   offers the 7:45 → long-press → **Rebook** → "Rebooked".
6. **Siri tracking**: "Hey Siri, track my shuttle with Clear Path".
7. **Chat on purpose**: Ask Clear Path → "Why can't I book Saturday?" →
   cited Booking Policy; "Should I leave now?" → weather step "via weather
   MCP server".
8. **MCP**: Claude Desktop → "Book my usual shuttle for Wednesday" → refresh
   app; "Book Saturday too" → refused.
9. **Under the hood**: Langfuse trace of the last chat turn; eval baseline
   (`backend/evals/baseline.json`, or a fresh `--cases` run if quota allows).
10. **Close** with the architecture slide.

After: `python -m scripts.demo_trip --stop`.
