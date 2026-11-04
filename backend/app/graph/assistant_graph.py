"""Conversational tool-calling agent.

    START → agent ──(tool calls?)──→ tools ──┐
              ↑                              │
              └──────────────────────────────┘
              └──(no tool calls)──→ END

The model decides which tools to call; LangGraph runs the loop and keeps
per-conversation memory through the checkpointer (thread_id =
conversation id). Business rules stay in the tools' services.
"""

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
- Never guess a booking_id or shuttle_id; take them from tool results. To
  book a new day, call book_usual_shuttle first, then adjust that booking.
- "It", "that ride" and similar refer to the booking discussed most
  recently in this conversation.
- To change a booking's time, call list_shuttle_options for its date, pick
  the shuttle that matches the request, then call change_booking_shuttle.
- Only cancel when the user explicitly asks to cancel.
- For "why can't I…" questions: call check_booking_eligibility for the
  date (use the date from the conversation if none is given), then call
  search_policies with that rule's message. Explain the real reason using
  the policy, mention which policy it comes from (for example "per the
  Booking Policy"), and suggest a concrete alternative.
- For "where's my shuttle" or "should I leave now", call get_shuttle_status.
  Pickup rules ask riders to be at the stop 5 minutes before the shuttle.
  For "should I leave now", start with a clear yes or no. If
  leave_in_minutes is present it already includes the walk to the stop:
  yes when it is 0 or less, otherwise say "leave in N minutes" and mention
  the walk time. Without it, answer yes if minutes_to_pickup is 10 or less.
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

    def agent(state: MessagesState, config: RunnableConfig):
        messages = [SystemMessage(system_prompt), *state["messages"]]

        # Each model gets the same deadline, so the worst case is bounded.
        # The config carries tracing callbacks into the worker thread.
        for position, attempt in enumerate(attempts):
            call = _model_calls.submit(attempt.invoke, messages, config)
            try:
                # Also raises TimeoutError when the deadline passes.
                response = call.result(timeout=deadline_seconds or MODEL_DEADLINE_SECONDS)
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
