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
10. Fallbacks ready: personal Shortcut, Type to Siri, recorded video.

## Script

1. **Siri booking** (phone locked/home): "Hey Siri, book my usual shuttle
   with Clear Path" → card → tap **Earlier**. *"No LLM call is needed when the
   request is already structured."*
2. **One tap**: Control Center button or widget **Book tomorrow** (reset or
   use another day first if already booked).
3. **Live trip**: `python -m scripts.demo_trip` → app → Where's my shuttle?
   → **Start trip mode** → lock the phone. Live Activity counts down;
   "Time to leave" arrives in ~1 minute.
4. **Delay**: `python -m scripts.demo_trip --delay 20` → notification
   offers the 7:45 → long-press → **Rebook** → "Rebooked".
5. **Siri tracking**: "Hey Siri, track my shuttle with Clear Path".
6. **Chat on purpose**: Ask Clear Path → "Why can't I book Saturday?" →
   cited Booking Policy; "Should I leave now?" → weather step "via weather
   MCP server".
7. **MCP**: Claude Desktop → "Book my usual shuttle for Wednesday" → refresh
   app; "Book Saturday too" → refused.
8. **Under the hood**: Langfuse trace of the last chat turn; eval baseline
   (`backend/evals/baseline.json`, or a fresh `--cases` run if quota allows).
9. **Close** with the architecture slide.

After: `python -m scripts.demo_trip --stop`.
