# AI: agent, models, RAG, evaluation, tracing

## Assistant agent (`app/graph/assistant_graph.py`, `app/api/assistant.py`)

```
START → agent ──(tool calls?)──→ tools (ToolNode) ──→ agent … → END
```

- Model chooses tools; LangGraph runs the loop; `RECURSION_LIMIT = 12`.
- Memory: LangGraph `PostgresSaver` (`app/agent/memory.py`), thread id
  `"{user_id}:{conversation_id}"` (users can't read each other's threads).
  The app/Siri share a conversation id stored in UserDefaults that expires
  after 30 minutes of inactivity.
- Each model call runs in a worker thread with an **8s deadline**
  (`MODEL_DEADLINE_SECONDS`); on error/timeout the next model in the
  fallback chain is tried with the same deadline. The run `config` is passed
  into the thread so tracing callbacks reach model calls.
- If a turn fails after a booking tool succeeded, the API still returns 200
  with "I made changes to your bookings…" (never hide a real change).
- The system prompt (`build_system_prompt`) carries today's date and rules:
  tools for every fact, ISO dates, never guess ids, book-then-adjust,
  "already booked" wording, why-flow (eligibility → policy search → cite →
  suggest nearest bookable day), leave-now yes/no using `leave_in_minutes`,
  weather check if available, offer faster alternative, answer policies
  only from search results, 1–2 spoken-friendly sentences, 12-hour times.

### Tools (`app/tools/assistant_tools.py`)

Bound to one user; booking errors return `{"error": …}`; all tools for a
session run one at a time (a lock — LangGraph runs parallel tool calls in
threads and the SQLAlchemy session isn't thread-safe).

`get_my_bookings`, `list_shuttle_options(date)`, `book_usual_shuttle(date)`,
`change_booking_shuttle(booking_id, shuttle_id)` (routes through
TrackingService.move_booking), `cancel_booking(booking_id)`,
`get_shuttle_status(booking_id?)` (phase, minutes, delay, walk, leave_in,
faster_alternative, pickup_coordinates; a simulated trip reports today's
date), `check_booking_eligibility(date)` (reason_code + message),
`search_policies(query)` (passages with similarity + `citable`).
`MUTATING_TOOLS` drive `bookings_changed`.

External MCP tools (weather) are appended at runtime; actions record the
providing server so the app labels them "· via weather MCP server".

## Models (Gemini, free tier only — never enable billing without asking)

| Role | Model | Why |
|---|---|---|
| Agent primary | `gemini-3.5-flash-lite` | ~1–2s; 3.1-flash-lite measured 20–47s and 503s under load (2026-11-02) |
| Fallbacks | `gemini-3.5-flash-lite` (fresh attempt), `gemini-3.1-flash-lite` | `gemini-3.5-flash` free tier = 20 requests/day |
| Thinking | `thinking_config={"thinking_level": "minimal"}` | cut per-call latency |
| Eval judge | `gemini-3.5-flash-lite` (`--judge-model`) | quota |
| Legacy intent extraction (`POST /bookings {message}`) | `gemini-3.1-flash-lite` in `app/agent/gemini_llm.py`, 10s timeout (Gemini rejects < 10s) | |

Notes: the langchain-google-genai `timeout` is not enforced (hence our own
deadline); Gemini 3.x ignores temperature; per-minute free limits cause 429s
during bursts.

## RAG (`app/rag/`, `backend/knowledge/`)

- Documents: booking policy, cancellation & changes, pickup rules, FAQ.
  One chunk per `## ` section (16 chunks), heading embedded with the body.
- Embeddings: fastembed `BAAI/bge-small-en-v1.5` (384-d, ONNX, local),
  cached in `backend/.cache/fastembed`; preloaded at startup.
- Storage: pgvector `knowledge_chunks`, HNSW cosine index.
- Thresholds live on the embedder (calibrated): `min_similarity = 0.60`
  (below = noise, not shown to the agent), `citation_min_similarity = 0.70`
  (only the top passage of a search is cited, if citable). Real questions
  scored 0.72–0.81; unrelated 0.52–0.56; "parking" → pickup points 0.68.
- Retrieval weakness: "3 weeks from now" ≠ "14 days"; the agent works around
  it by searching with the rule message from `check_booking_eligibility`.
- After editing a policy: `python -m scripts.ingest_knowledge`.

## Evaluation (`backend/evals/`)

`python -m evals.run` — 24 cases (`dataset.json`) across booking,
follow-up, rules-rag, tracking, safety. Each case: optional setup
(bookings by day offset/departure, simulation), user turns, expectations
(`tools_called`, `tools_not_called`, exact final `bookings`, `sources`,
`rubric`). Runs in `<db>_eval` at fixed Monday 2026-11-02 06:00 with real
embeddings and Gemini; LLM judge (`evals/judge.py`) scores 1–5 against the
rubric and the tool results (unsupported facts ≤ 2), told the run's date.

Options: `--cases a,b`, `--model`, `--fallback a,b`, `--no-fallback`,
`--judge-model`, `--pause 6` (rate limits), `--save-baseline`, `--check`
(fails if task success drops > 5 points). Results go to `evals/results/`
(git-ignored) and, when Langfuse is configured, each case is a trace tagged
`eval` with `task_success`, `judge_score`, `tool_choice` scores.

**Baseline (2026-11-04, gemini-3.5-flash-lite):** task success 91.7%
(22/24), tool accuracy 100%, judge 4.67/5, p50 6.8s, p95 25.9s, ~$0.0014
per task estimated (free tier, not billed). Known failures:
`book-sunday-refused` (judge miscount — reply was right) and
`delay-offers-alternative` (agent said pickup 8:10 instead of 7:50).

A full run is ~100 free requests and shares the app's daily quota — don't
run it repeatedly, especially on demo day.

## Tracing (`app/observability/tracing.py`, `observability/`)

Self-hosted Langfuse v4 (web UI http://localhost:3000; login in
`observability/.env`: `LANGFUSE_INIT_USER_EMAIL` / `..._PASSWORD`; running
`python3 observability/setup_env.py` again prints it without changes).
Each assistant turn is an `assistant-turn` trace (session = conversation,
user = 1) with model generations and tool spans. v4 runs "events only":
the old `/api/public/traces` read API is gone; use the UI,
`/api/public/v2/observations`, or ClickHouse
(`docker exec langfuse-clickhouse-1 clickhouse-client --user clickhouse
--password <CLICKHOUSE_PASSWORD> …`). Telemetry is off; Langfuse's own AI
features are unconfigured so nothing leaves the Mac.
