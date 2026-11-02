"""Evaluate the assistant agent against evals/dataset.json.

Each case runs against the real agent and model in an isolated database
at a fixed moment (Monday 2 November 2026, 6:00 AM), then is scored on:

  task success  final bookings are exactly as expected
  tool choice   expected tools called, forbidden tools not called
  citations     cited policy sections, where the case specifies them
  answer        an LLM judge grades the reply against a rubric and the
                tool results (catches hallucinated facts)

plus latency, tokens, cost, and how often the fallback model answered.

    python -m evals.run                         # all cases, configured models
    python -m evals.run --cases why-not-saturday,leave-now
    python -m evals.run --model gemini-3.1-flash-lite --no-fallback
    python -m evals.run --save-baseline         # record as the new baseline
    python -m evals.run --check                 # fail on regression vs baseline
"""

import argparse
import json
import statistics
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from app.isolated_database import assert_isolated, use_isolated_database

# Before any app import reads DATABASE_URL.
EVAL_DATABASE = use_isolated_database("eval")

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage  # noqa: E402
from langgraph.checkpoint.memory import InMemorySaver  # noqa: E402
from sqlalchemy import select, text  # noqa: E402

from app.agent.factory import create_chat_model  # noqa: E402
from app.api.assistant import _sources_in  # noqa: E402
from app.core import clock  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.database import SessionLocal, engine  # noqa: E402

# Evaluations drop and reseed every table; never against the demo database.
assert_isolated(engine.url, "eval")
from app.db.seed import seed_database  # noqa: E402
from app.graph.assistant_graph import (  # noqa: E402
    RECURSION_LIMIT,
    build_system_prompt,
    create_assistant_graph,
)
from app.models.booking import Booking  # noqa: E402
from app.models.shuttle import Shuttle  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.user_location import UserLocation  # noqa: E402
from app.rag.embeddings import get_embedder  # noqa: E402
from app.rag.ingest import ingest_knowledge  # noqa: E402
from app.repositories.booking_repository import BookingRepository  # noqa: E402
from app.repositories.preference_repository import PreferenceRepository  # noqa: E402
from app.repositories.shuttle_repository import ShuttleRepository  # noqa: E402
from app.repositories.user_repository import UserRepository  # noqa: E402
from app.services.booking_service import BookingService  # noqa: E402
from app.services.tracking_service import TrackingService  # noqa: E402
from app.tools.assistant_tools import create_assistant_tools  # noqa: E402
from app.observability import tracing  # noqa: E402
from evals.judge import judge  # noqa: E402


EVALS_DIR = Path(__file__).resolve().parent
DATASET = EVALS_DIR / "dataset.json"
BASELINE = EVALS_DIR / "baseline.json"
RESULTS_DIR = EVALS_DIR / "results"

FIXED_NOW = datetime(2026, 11, 2, 6, 0)  # a Monday, before the first shuttle
# gemini-3.5-flash allows only 20 requests/day on the free tier, so the
# judge defaults to Flash-Lite; --judge-model overrides it.
JUDGE_MODEL = "gemini-3.5-flash-lite"
# A drop in task success larger than this (one case in 24) fails --check.
ALLOWED_SUCCESS_DROP = 0.05

# USD per 1M tokens (input, output); snapshot from the LLM architecture
# doc, 2026-09-30.
PRICES = {
    "gemini-3.1-flash-lite": (0.25, 1.50),
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "gemini-3.5-flash": (1.50, 9.00),
}


@dataclass
class CaseResult:
    id: str
    category: str
    passed: bool
    checks: dict[str, bool]
    judge_score: int
    judge_reason: str
    reply: str
    tools: list[str]
    bookings: list[dict]
    latency_seconds: float
    input_tokens: int
    output_tokens: int
    cost_usd: float
    model_calls: dict[str, int] = field(default_factory=dict)
    error: str | None = None


def prepare_database() -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_database()
    with SessionLocal() as db:
        # Real embeddings: retrieval quality is part of what's measured.
        ingest_knowledge(db, get_embedder())


def booking_service(db) -> BookingService:
    return BookingService(
        db=db,
        user_repository=UserRepository(db),
        preference_repository=PreferenceRepository(db),
        shuttle_repository=ShuttleRepository(db),
        booking_repository=BookingRepository(db),
    )


def reset_and_set_up(db, user_id: int, setup: dict) -> None:
    db.query(Booking).delete()  # trip simulations cascade
    db.query(UserLocation).delete()
    db.commit()

    service = booking_service(db)
    tracking = TrackingService(db, service)
    shuttles = {f"{s.departure_time:%H:%M}": s for s in db.scalars(select(Shuttle))}
    today = FIXED_NOW.date()

    for spec in setup.get("bookings", []):
        booking = service.book_usual_shuttle(user_id, today + timedelta(days=spec["day"])).booking
        if spec["departure"] != f"{booking.shuttle.departure_time:%H:%M}":
            service.move_booking(user_id, booking.id, shuttles[spec["departure"]].id)

    simulation = setup.get("simulation")
    if simulation:
        booking = service.get_upcoming_bookings(user_id)[0]
        tracking.start_simulation(
            user_id,
            booking.id,
            start_minutes=simulation["start_minutes"],
            walk_minutes=simulation.get("walk_minutes"),
        )
        if simulation.get("delay_minutes"):
            tracking.set_delay(user_id, booking.id, simulation["delay_minutes"])


def final_bookings(db, user_id: int) -> list[dict]:
    today = FIXED_NOW.date()
    return sorted(
        (
            {"day": (b.booking_date - today).days, "departure": f"{b.shuttle.departure_time:%H:%M}"}
            for b in booking_service(db).get_upcoming_bookings(user_id)
        ),
        key=lambda b: (b["day"], b["departure"]),
    )


def run_case(case: dict, model_name: str, fallback_names: list[str], judge_model, run_id: str) -> CaseResult:
    expect = case["expect"]

    with SessionLocal() as db:
        user = db.scalar(select(User))
        reset_and_set_up(db, user.id, case.get("setup", {}))

        graph = create_assistant_graph(
            model=create_chat_model(model_name),
            tools=create_assistant_tools(db, user.id, get_embedder()),
            checkpointer=InMemorySaver(),
            system_prompt=build_system_prompt(FIXED_NOW.date(), user.name),
            fallback_models=[create_chat_model(name) for name in fallback_names],
        )
        config = {"configurable": {"thread_id": case["id"]}, "recursion_limit": RECURSION_LIMIT}

        started = time.monotonic()
        error = None
        messages = []
        # One trace per case in Langfuse (when configured), tagged so eval
        # runs can be filtered and compared there.
        with tracing.traced(
            f"eval:{case['id']}",
            user_id=user.id,
            session_id=f"eval-{run_id}",
            input=case["turns"],
            tags=["eval", case["category"], model_name],
        ) as trace:
            try:
                for turn in case["turns"]:
                    messages = graph.invoke(
                        {"messages": [HumanMessage(turn)]},
                        config={**config, "callbacks": trace.callbacks},
                    )["messages"]
            except Exception as e:
                error = f"{type(e).__name__}: {e}"[:300]
            trace.finish(messages[-1].text if messages else error)
        latency = time.monotonic() - started

        bookings = final_bookings(db, user.id)

    ai_messages = [m for m in messages if isinstance(m, AIMessage)]
    tools = [call["name"] for m in ai_messages for call in m.tool_calls]
    tool_results = [(m.name, m.text) for m in messages if isinstance(m, ToolMessage)]
    reply = messages[-1].text if messages and isinstance(messages[-1], AIMessage) else ""
    last_human = max((i for i, m in enumerate(messages) if isinstance(m, HumanMessage)), default=0)

    input_tokens = output_tokens = 0
    cost = 0.0
    model_calls: dict[str, int] = {}
    for message in ai_messages:
        usage = message.usage_metadata or {}
        name = message.response_metadata.get("model_name", "unknown")
        model_calls[name] = model_calls.get(name, 0) + 1
        input_tokens += usage.get("input_tokens", 0)
        output_tokens += usage.get("output_tokens", 0)
        price_in, price_out = PRICES.get(name, (0, 0))
        cost += (usage.get("input_tokens", 0) * price_in + usage.get("output_tokens", 0) * price_out) / 1e6

    checks = {"completed": error is None}
    if "tools_called" in expect:
        checks["tools_called"] = set(expect["tools_called"]) <= set(tools)
    if "tools_not_called" in expect:
        checks["tools_not_called"] = not set(expect["tools_not_called"]) & set(tools)
    if "bookings" in expect:
        checks["bookings"] = bookings == sorted(expect["bookings"], key=lambda b: (b["day"], b["departure"]))
    if "sources" in expect:
        checks["sources"] = _sources_in(messages[last_human + 1:]) == expect["sources"]

    score, reason = 1, "Not judged: the run failed."
    if error is None:
        try:
            verdict = judge(judge_model, case["turns"], reply, tool_results, expect["rubric"])
            score, reason = verdict.score, verdict.reason
            checks["answer"] = verdict.passed
        except Exception as e:
            # Can't call it a success without a verdict, but one judge
            # error (e.g. a quota limit) shouldn't stop the whole run.
            reason = f"Not judged: {type(e).__name__}: {e}"[:300]
            checks["judged"] = False

    passed = all(checks.values())
    tracing.score(trace.trace_id, "task_success", float(passed), ", ".join(k for k, ok in checks.items() if not ok) or None)
    tracing.score(trace.trace_id, "judge_score", score, reason)
    if any(k in checks for k in ("tools_called", "tools_not_called")):
        tracing.score(
            trace.trace_id,
            "tool_choice",
            float(checks.get("tools_called", True) and checks.get("tools_not_called", True)),
        )

    return CaseResult(
        id=case["id"],
        category=case["category"],
        passed=passed,
        checks=checks,
        judge_score=score,
        judge_reason=reason,
        reply=reply,
        tools=tools,
        bookings=bookings,
        latency_seconds=round(latency, 2),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=round(cost, 6),
        model_calls=model_calls,
        error=error,
    )


def summarize(results: list[CaseResult], model_name: str) -> dict:
    latencies = sorted(r.latency_seconds for r in results)
    by_category: dict[str, list[CaseResult]] = {}
    for r in results:
        by_category.setdefault(r.category, []).append(r)

    calls: dict[str, int] = {}
    for r in results:
        for name, count in r.model_calls.items():
            calls[name] = calls.get(name, 0) + count
    total_calls = sum(calls.values()) or 1

    tool_checks = [
        ok for r in results for name, ok in r.checks.items()
        if name in ("tools_called", "tools_not_called")
    ]

    return {
        "model": model_name,
        "cases": len(results),
        "task_success": round(sum(r.passed for r in results) / len(results), 3),
        "tool_accuracy": round(sum(tool_checks) / len(tool_checks), 3) if tool_checks else None,
        "mean_judge_score": round(statistics.mean(r.judge_score for r in results), 2),
        # Judged replies scored 2 or lower: wrong or unsupported by tools.
        "hallucination_flags": sum("answer" in r.checks and r.judge_score <= 2 for r in results),
        "latency_p50_s": round(statistics.median(latencies), 2),
        "latency_p95_s": round(latencies[max(0, round(0.95 * len(latencies)) - 1)], 2),
        "mean_cost_per_task_usd": round(statistics.mean(r.cost_usd for r in results), 6),
        "fallback_share": round(1 - calls.get(model_name, 0) / total_calls, 3),
        "by_category": {
            name: round(sum(r.passed for r in rs) / len(rs), 3) for name, rs in sorted(by_category.items())
        },
    }


def print_report(results: list[CaseResult], summary: dict) -> None:
    print(f"\n{'case':28} {'ok':3} {'judge':5} {'time':>6}  checks failed")
    for r in results:
        failed = ", ".join(name for name, ok in r.checks.items() if not ok)
        print(f"{r.id:28} {'✓' if r.passed else '✗':3} {r.judge_score:>3}/5 {r.latency_seconds:>5.1f}s  {failed}")
        if not r.passed:
            print(f"{'':28}     judge: {r.judge_reason}")
            if r.error:
                print(f"{'':28}     error: {r.error}")

    print("\nSummary")
    for key, value in summary.items():
        print(f"  {key:24} {value}")


def check_against_baseline(results: list[CaseResult], summary: dict) -> bool:
    if not BASELINE.exists():
        print("\nNo baseline yet; run with --save-baseline first.")
        return False

    baseline = json.loads(BASELINE.read_text())
    regressions = [
        r.id for r in results
        if baseline["passed"].get(r.id) and not r.passed
    ]
    drop = baseline["summary"]["task_success"] - summary["task_success"]

    print(f"\nBaseline task success {baseline['summary']['task_success']:.1%}, now {summary['task_success']:.1%}")
    if regressions:
        print("Cases that passed in the baseline but failed now:", ", ".join(regressions))

    ok = drop <= ALLOWED_SUCCESS_DROP
    print("PASS" if ok else f"FAIL: task success dropped by {drop:.1%} (allowed {ALLOWED_SUCCESS_DROP:.0%})")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the Clear Path assistant agent.")
    parser.add_argument("--model", default=settings.agent_model)
    parser.add_argument(
        "--fallback",
        default=",".join(settings.agent_fallback_models),
        help="comma-separated fallback models, tried in order",
    )
    parser.add_argument("--no-fallback", action="store_true")
    parser.add_argument("--judge-model", default=JUDGE_MODEL)
    parser.add_argument("--cases", help="comma-separated case ids")
    parser.add_argument("--save-baseline", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    cases = json.loads(DATASET.read_text())
    if args.cases:
        wanted = set(args.cases.split(","))
        cases = [c for c in cases if c["id"] in wanted]

    clock.now = lambda: FIXED_NOW
    prepare_database()
    judge_model = create_chat_model(args.judge_model)
    fallbacks = [] if args.no_fallback else [m for m in args.fallback.split(",") if m]

    print(f"Evaluating {len(cases)} cases on {args.model}"
          + (f" (fallbacks {', '.join(fallbacks)})" if fallbacks else "") + f", database {EVAL_DATABASE}")
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    results = []
    for case in cases:
        result = run_case(case, args.model, fallbacks, judge_model, run_id)
        print(f"  {'✓' if result.passed else '✗'} {case['id']}", flush=True)
        results.append(result)

    summary = summarize(results, args.model)
    print_report(results, summary)

    tracing.flush()

    RESULTS_DIR.mkdir(exist_ok=True)
    report = {"summary": summary, "results": [asdict(r) for r in results]}
    (RESULTS_DIR / f"{run_id}-{args.model}.json").write_text(json.dumps(report, indent=2, default=str))

    if args.save_baseline:
        BASELINE.write_text(json.dumps(
            {"summary": summary, "passed": {r.id: r.passed for r in results}}, indent=2
        ))
        print(f"\nSaved baseline: {BASELINE.relative_to(EVALS_DIR.parent)}")

    if args.check:
        return 0 if check_against_baseline(results, summary) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
