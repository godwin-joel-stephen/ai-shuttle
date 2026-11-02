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
