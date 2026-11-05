# Backend

Python 3.14 (Homebrew) in `backend/.venv`. FastAPI + SQLAlchemy 2 +
psycopg 3, LangGraph 1.2, langchain-core 1.6.6 (pinned; newer google-genai
majors were avoided), Postgres 17 with pgvector. Dependencies are pinned in
`backend/requirements.txt`; install with `pip install -r requirements.txt`.

## Configuration (`app/core/config.py`, read from `backend/.env`)

| Setting | Default / notes |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg://ai_shuttle:…@localhost:5432/ai_shuttle` |
| `GEMINI_API_KEY` | free-tier key |
| `AGENT_MODEL` | `gemini-3.5-flash-lite` |
| `AGENT_FALLBACK_MODELS` | `["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]` |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` | tracing off unless both keys set (added by `observability/setup_env.py`) |
| `MCP_SERVERS` | `{"weather": {"command": "python", "args": ["-m","mcp_servers.weather"]}}`; `'{}'` disables |

`.env` files are git-ignored. `app.core.clock.now()` is the only source of
time; tests/evals monkeypatch it.

## Endpoints

| Method & path | Purpose |
|---|---|
| `GET /health` | liveness |
| `GET /bookings?user_id=1` | upcoming confirmed bookings |
| `GET /bookings/{id}?user_id=1` | one booking + `earlier_available` / `later_available` |
| `POST /bookings` | `{user_id, booking_date}` structured (no LLM) **or** `{user_id, message}` natural language; idempotent (returns `already_booked`) |
| `POST /bookings/{id}/reschedule` | `{user_id, direction: earlier|later}` (Siri card buttons) |
| `POST /bookings/{id}/move` | `{user_id, shuttle_id}`; returns trip status; keeps a running simulation aligned |
| `POST /assistant/messages` | `{user_id, message, conversation_id?}` → `{conversation_id, reply, actions[{tool, arguments, succeeded, error, server}], bookings_changed, sources[]}` |
| `GET /assistant/conversations/{id}?user_id=1` | replay a conversation (Siri turns show in the app) |
| `GET /tracking/next?user_id=1` | live status of the next (or simulated) trip |
| `GET /bookings/{id}/tracking` | live status of a booking |
| `POST /schedule/plan` | `{user_id, days: [{date, kind: office|remote|offsite|leave}]}` (1–31 unique dates) → per day `action` book/keep/cancel/none/blocked + `message`, `reason_code`, `bookings`; `summary`, `changes`. Changes nothing |
| `POST /schedule/apply` | same body (only the days the user approved) → re-plans, books/cancels, per-day `succeeded`; `summary`, `bookings_changed` |
| `POST /users/{id}/location` | `{latitude, longitude}` from trip mode (204) |
| `POST /simulator/trips/{id}` | `{start_minutes, speed, walk_minutes?}` replay a trip now |
| `POST /simulator/trips/{id}/delay` | `{minutes}` |
| `DELETE /simulator/trips/{id}` | stop replaying |

Errors: `NotFoundError` → 404, other `BookingError` → 409, model failure →
503. `detail` is user-facing (Siri reads it aloud).

## Data model (`app/models/`)

`users`, `routes`, `shuttles`, `preferences` (usual shuttle), `bookings`
(`status` confirmed/cancelled), `knowledge_chunks` (pgvector 384-d, HNSW
cosine index), `trip_simulations` (per booking: started_at, start_minutes,
speed, delay_minutes, walk_minutes; cascades with booking), `user_locations`.
LangGraph's `PostgresSaver` adds its own checkpoint tables.

Seed (`app/db/seed.py`): user 1 "Godwin Joel"; route *Home → Office Morning*
with Morning Shuttle A–E departing 7:00, 7:15, **7:30 (usual, C)**, 7:45,
8:00 (45-minute trips, 10 seats); evening route Office → Home 17:30, 18:00.
`create_all` never alters tables: after model changes run
`scripts/rebuild_demo_db.py` (drops everything incl. conversations) or an
`ALTER TABLE` on the dev DB.

## Booking rules (`app/services/booking_service.py`, explained in `knowledge/booking_policy.md` — keep in sync)

- Service Monday–Friday only (`NoServiceDayError`)
- Booking window 14 days (`OutsideBookingWindowError`)
- Same-day cut-off 30 min before departure (`BookingCutoffPassedError`)
- Past dates (`DatePassedError`), full shuttle (`ShuttleUnavailableError`, 10 seats)
- One confirmed booking per route per day: booking again returns the
  existing one (`already_booked`)
- `check_eligibility` explains a failure without booking; moves validate the
  target shuttle with the same rules.

## Schedule import (`app/services/schedule_service.py`, `app/api/schedule.py`)

The phone sends typed days only (no document text). Office day → book the
usual shuttle (or *keep* if booked, *blocked* with the rule's message and
`reason_code` if a booking rule fails); remote/offsite/leave → cancel every
confirmed booking that day on any route (except shuttles that already
left), else *none*. Past dates are *blocked* (`date_passed`). Apply
re-plans first, so a day booked meanwhile isn't booked twice, and reports
each day's success separately (a failed day never hides the others). No
LLM: `ScheduleService` sits on `BookingService`, so every rule is shared.

## Trip planner (`app/services/trip_planner.py`, F7)

`TripPlanner.plan/apply(user_id, dates, TripGoal(arrive_by?, leave_after?))`
→ per day `DayPlan` with action **keep** (current booking already meets
the goal), **book**, **move** (existing booking too late), **not_possible**
(nothing meets it: `best_effort` = soonest usable arrival, `late_by_minutes`)
or **blocked** (day-level rule; `nearby_days` = closest workable days
before/after, ≤7 days). Options come from `day_options`: every shuttle on
the route with expected arrival (current trip includes its live delay),
booking-rule problem (`BookingService.departure_problem`: full, cut-off…)
and catchability (lead time > walk + 5-min pickup buffer, measured on the
current trip's timeline when there is one, so simulations work). Choice:
current if on time → usual if on time → latest departure meeting an
arrive-by goal (earliest after a leave-after goal). Apply books
(`BookingService.book_shuttle`, new: any shuttle, same idempotence) or
moves (`TrackingService.move_booking`); not_possible days are never
"fixed" with a late shuttle. F4's `TrackingService._alternative` uses the
same `day_options` + `faster_alternative`.

## Tracking (`app/services/tracking_service.py`)

Timeline in minutes from scheduled departure t: scheduled (t < −15),
approaching (−15 ≤ t < delay), boarding (2 min), in_transit, arrived. ETAs
are returned as real wall-clock times (whole seconds, with UTC offset) so the
phone can count down. With a `TripSimulation`, t = start_minutes +
elapsed × speed. Enrichment adds walk minutes (simulation `walk_minutes`, or
GPS within 15 min: distance × 1.3 at 4.8 km/h), `leave_in_minutes` (to
pickup − walk − 5 min buffer) and a faster catchable alternative when
delayed. Route geometry: approximate Bengaluru polyline (Indiranagar →
Manyata Tech Park) in `route_geometry.py`.

## Scripts (`backend/scripts`)

| Command | Use |
|---|---|
| `python -m scripts.demo_trip` | books next weekday if needed and replays it now; defaults `--start -11 --walk 4 --speed 2` ("Time to leave" ~1 min after trip mode starts); `--delay 20`, `--stop`, `--walk 0` = use GPS |
| `python -m scripts.reset_demo_db` | delete bookings (simulations cascade) and locations |
| `python -m scripts.rebuild_demo_db` | drop schema, recreate, seed, ingest policies |
| `python -m scripts.ingest_knowledge` | re-embed `knowledge/*.md` after editing a policy |
| `python -m app.db.init_db` | create missing tables (+ vector extension) |

## Tests (`backend/tests`, 103 tests, ~8s, no network)

- `conftest.py` switches to `<db>_test` via `app.isolated_database` before
  any `app.db` import, asserts it, rebuilds schema each session, seeds,
  ingests policies with `FakeEmbedder`, pins the clock to Monday
  2026-11-02 06:00 (`FIXED_NOW`, `TODAY`, `TOMORROW`), disables tracing,
  and cleans bookings/locations after each test.
- `ScriptedChatModel` (tests/scripted_chat_model.py) replays scripted
  AIMessages/callables in place of Gemini; `call(name, **args)` builds tool
  calls.
- MCP client tests launch the real MCP server over stdio against the test DB.
- `tests/manual_gemini_*.py` are manual live checks, not collected by pytest.
