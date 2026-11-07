"""Conversational tool-calling agent.

    START → agent ──(tool calls?)──→ tools ──┐
              ↑                              │
              └──────────────────────────────┘
              └──(no tool calls)──→ END

The model decides which tools to call; LangGraph runs the loop and keeps
per-conversation memory through the checkpointer (thread_id =
conversation id). Business rules stay in the tools' services.
"""

import re
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import date

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition


# Upper bound on agent/tool steps per message, so a confused model can't
# loop forever.
RECURSION_LIMIT = 12

# Per model call. The Gemini client's own timeout isn't enforced (calls ran
# 30-45s with it set to 10s), so the agent enforces one and moves on to the
# fallback model instead of waiting for an overloaded model to give up.
MODEL_DEADLINE_SECONDS = 8

# A timed-out call keeps running in its thread until the HTTP request
# returns; it is abandoned, not cancelled.
_model_calls = ThreadPoolExecutor(max_workers=8, thread_name_prefix="model-call")


class UnusableReplyError(RuntimeError):
    """The model answered with something that isn't a reply to a person."""


def is_unusable_reply(message, tool_names: frozenset[str]) -> bool:
    """A final reply that must never reach the rider. Flash-Lite once
    answered a habits question with the bare text
    "ValueOfget_commute_habits", which Siri read out as the answer."""

    if getattr(message, "tool_calls", None):
        return False
    text = message.text.strip()
    if not text:
        return True
    # Internal tool names are never part of a good answer.
    if any(name in text for name in tool_names):
        return True
    # A lone code-like identifier (snake_case or camelCase) isn't a sentence.
    return bool(
        re.fullmatch(r"[A-Za-z_][\w.()]*", text)
        and ("_" in text or re.search(r"[a-z][A-Z]", text))
    )


def build_system_prompt(today: date, user_name: str) -> str:
    return f"""You are Clear Path, a shuttle booking assistant for {user_name}.
Today is {today:%A, %B %-d, %Y} ({today.isoformat()}).

Rules:
- Use the tools for every fact about bookings and shuttles. Never invent
  bookings, shuttles, times or availability.
- Resolve relative dates ("tomorrow", "Friday", "next Monday") against
  today's date and pass dates as YYYY-MM-DD.
- If book_usual_shuttle returns already_booked=true, tell the user they were
  already booked on that shuttle; never describe it as a new booking.
- The usual shuttle can differ by weekday: it is learned from the user's
  recent rides unless they pinned one. Only when book_usual_shuttle
  returns usual_because, mention it briefly, using its words ("your usual
  Monday 7:15 AM, since " + usual_because). Without usual_because, give
  no reason and never make up ride history. For "what's my usual" or
  "why that shuttle", call get_commute_habits. To make a shuttle the
  usual ("make the 7:45 my usual"), call list_shuttle_options, then
  set_usual_shuttle; it changes no existing bookings.
- Never guess a booking_id or shuttle_id; take them from tool results. To
  book a new day, call book_usual_shuttle first, then adjust that booking.
- "It", "that ride" and similar refer to the booking discussed most
  recently in this conversation.
- To change a booking's time, call list_shuttle_options for its date, pick
  the shuttle that matches the request, then call change_booking_shuttle.
- Arrival or departure goals ("get me to the office by 8:30", "I have a
  meeting at 9", "not before 7:40", "every day this week"): a meeting or
  start time is arrive_by. Statements of need ("I need to be…", "get me
  to…", "make sure I…", "I have a meeting at…") are requests to arrange
  it: call book_trip_plan once with every date, without asking first.
  Only a question about whether it works ("will I make it by…?", "can I
  get there by…?") calls plan_trip. Don't use book_usual_shuttle or
  change_booking_shuttle for goals. Quote departure and arrival times
  exactly as the result gives them, and mention any unavailable shuttle
  and why (for example, full). If a day is not_possible, say no shuttle
  gets there in time, give soonest_possible and how late it is, and offer
  to book it (or switch to it, if it isn't the current booking); never
  book or move for it unless the user agrees.
- Only cancel when the user explicitly asks to cancel.
- For "why can't I…" questions: call check_booking_eligibility for the
  date (use the date from the conversation if none is given), then call
  search_policies with that rule's message. Explain the real reason using
  the policy, mention which policy it comes from (for example "per the
  Booking Policy"), and suggest a concrete alternative.
- For "where's my shuttle" or "should I leave now", call get_shuttle_status.
  Pickup rules ask riders to be at the stop 5 minutes before the shuttle.
  For "should I leave now", start with "Yes" exactly when leave_now is
  true and "No" when it is false. When it is false and leave_in_minutes is
  present, say "leave in N minutes" (it already includes the walk to the
  stop) and mention the walk time.
- If a get_current_weather tool is available, also check the weather at
  the pickup_coordinates for "should I leave now". If it's raining or the
  rain chance is 50% or more, suggest an umbrella and leaving a couple of
  minutes earlier.
- If the shuttle is late and faster_alternative is present, mention it
  and offer to move the booking (change_booking_shuttle).
- For questions about rules, cancellations, pickups or luggage, answer only
  from search_policies results. If nothing relevant comes back, say you
  don't know rather than guessing.
- If a tool returns an error, explain it plainly and suggest an option.
  When a booking can't be made for a date, always name the nearest day
  that can be booked.
- Reply in one or two short sentences that read well aloud, with times in
  12-hour format (for example 7:30 AM)."""


def create_assistant_graph(
    model: BaseChatModel,
    tools: list[BaseTool],
    checkpointer: BaseCheckpointSaver,
    system_prompt: str,
    fallback_models: Sequence[BaseChatModel] = (),
    deadline_seconds: float | None = None,
):
    attempts = [m.bind_tools(tools) for m in (model, *fallback_models)]
    tool_names = frozenset(t.name for t in tools)

    def agent(state: MessagesState, config: RunnableConfig):
        messages = [SystemMessage(system_prompt), *state["messages"]]

        # Each model gets the same deadline, so the worst case is bounded.
        # The config carries tracing callbacks into the worker thread.
        for position, attempt in enumerate(attempts):
            call = _model_calls.submit(attempt.invoke, messages, config)
            try:
                # Also raises TimeoutError when the deadline passes.
                response = call.result(timeout=deadline_seconds or MODEL_DEADLINE_SECONDS)
                # A garbled reply is a failure like a timeout: the next
                # model gets a fresh attempt instead of the rider hearing it.
                if is_unusable_reply(response, tool_names):
                    raise UnusableReplyError(response.text[:200])
                break
            except Exception:
                if position == len(attempts) - 1:
                    raise

        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition, ["tools", END])
    graph.add_edge("tools", "agent")

    return graph.compile(checkpointer=checkpointer)
