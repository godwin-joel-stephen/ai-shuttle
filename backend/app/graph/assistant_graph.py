"""Conversational tool-calling agent.

    START → agent ──(tool calls?)──→ tools ──┐
              ↑                              │
              └──────────────────────────────┘
              └──(no tool calls)──→ END

The model decides which tools to call; LangGraph runs the loop and keeps
per-conversation memory through the checkpointer (thread_id =
conversation id). Business rules stay in the tools' services.
"""

from datetime import date

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition


# Upper bound on agent/tool steps per message, so a confused model can't
# loop forever.
RECURSION_LIMIT = 12


def build_system_prompt(today: date, user_name: str) -> str:
    return f"""You are Clear Path, a shuttle booking assistant for {user_name}.
Today is {today:%A, %B %-d, %Y} ({today.isoformat()}).

Rules:
- Use the tools for every fact about bookings and shuttles. Never invent
  bookings, shuttles, times or availability.
- Resolve relative dates ("tomorrow", "Friday", "next Monday") against
  today's date and pass dates as YYYY-MM-DD.
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
- If the shuttle is late and faster_alternative is present, mention it
  and offer to move the booking (change_booking_shuttle).
- For questions about rules, cancellations, pickups or luggage, answer only
  from search_policies results. If nothing relevant comes back, say you
  don't know rather than guessing.
- If a tool returns an error, explain it plainly and suggest an option.
- Reply in one or two short sentences that read well aloud, with times in
  12-hour format (for example 7:30 AM)."""


def create_assistant_graph(
    model: BaseChatModel,
    tools: list[BaseTool],
    checkpointer: BaseCheckpointSaver,
    system_prompt: str,
    fallback_model: BaseChatModel | None = None,
):
    model_with_tools = model.bind_tools(tools)

    if fallback_model is not None:
        model_with_tools = model_with_tools.with_fallbacks(
            [fallback_model.bind_tools(tools)]
        )

    def agent(state: MessagesState):
        response = model_with_tools.invoke(
            [SystemMessage(system_prompt), *state["messages"]]
        )
        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition, ["tools", END])
    graph.add_edge("tools", "agent")

    return graph.compile(checkpointer=checkpointer)
