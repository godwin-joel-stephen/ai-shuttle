import json
import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from sqlalchemy.orm import Session

from app.agent.factory import create_chat_model
from app.agent.memory import get_checkpointer
from app.core import clock
from app.core.config import settings
from app.db.database import get_db
from app.graph.assistant_graph import (
    RECURSION_LIMIT,
    build_system_prompt,
    create_assistant_graph,
)
from app.rag.embeddings import Embedder, get_embedder
from app.repositories.user_repository import UserRepository
from app.schemas.assistant import (
    AssistantAction,
    AssistantMessageRequest,
    AssistantMessageResponse,
    ConversationMessage,
    ConversationResponse,
)
from app.tools.assistant_tools import MUTATING_TOOLS, create_assistant_tools


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/assistant",
    tags=["assistant"],
)


def get_chat_model() -> BaseChatModel:
    return create_chat_model()


def get_fallback_chat_model() -> BaseChatModel | None:
    return create_chat_model(settings.agent_fallback_model)


def get_conversation_memory() -> BaseCheckpointSaver:
    return get_checkpointer()


def get_policy_embedder() -> Embedder:
    return get_embedder()


def get_external_tools(request: Request) -> list[BaseTool]:
    """Tools discovered from external MCP servers at startup."""

    return getattr(request.app.state, "external_tools", [])


def _thread_config(user_id: int, conversation_id: str) -> dict:
    # Prefix with the user id so one user can never read or continue
    # another user's conversation.
    return {"configurable": {"thread_id": f"{user_id}:{conversation_id}"}}


def _tool_servers(tools: list[BaseTool]) -> dict[str, str]:
    """Tool name -> external MCP server, for tools that came from one."""

    return {
        tool.name: tool.metadata["mcp_server"]
        for tool in tools
        if tool.metadata and "mcp_server" in tool.metadata
    }


def _sources_in(turn: list) -> list[str]:
    """Best-matching policy section of each policy search, in order.

    Only a confident top result is cited: lower-ranked or weaker passages
    are often near-misses, and citing them would misattribute the answer.
    """

    sources = []
    for message in turn:
        if not isinstance(message, ToolMessage) or message.name != "search_policies":
            continue
        try:
            passages = json.loads(message.text).get("passages", [])
        except ValueError:
            continue
        if not passages or not passages[0]["citable"]:
            continue
        if passages[0]["source"] not in sources:
            sources.append(passages[0]["source"])

    return sources


def _actions_in(turn: list, servers: dict[str, str] | None = None) -> list[AssistantAction]:
    results = {
        m.tool_call_id: m for m in turn if isinstance(m, ToolMessage)
    }

    actions = []
    for message in turn:
        if not isinstance(message, AIMessage):
            continue

        for call in message.tool_calls:
            result = results.get(call["id"])
            error = None

            if result is None or result.status == "error":
                error = result.text if result else "Tool did not run."
            else:
                try:
                    payload = json.loads(result.text)
                except ValueError:
                    payload = {}
                if isinstance(payload, dict):
                    error = payload.get("error")

            actions.append(
                AssistantAction(
                    tool=call["name"],
                    arguments=call["args"],
                    succeeded=error is None,
                    error=error,
                    server=(servers or {}).get(call["name"]),
                )
            )

    return actions


@router.post("/messages", response_model=AssistantMessageResponse)
def send_message(
    request: AssistantMessageRequest,
    db: Session = Depends(get_db),
    model: BaseChatModel = Depends(get_chat_model),
    fallback_model: BaseChatModel | None = Depends(get_fallback_chat_model),
    memory: BaseCheckpointSaver = Depends(get_conversation_memory),
    embedder: Embedder = Depends(get_policy_embedder),
    external_tools: list[BaseTool] = Depends(get_external_tools),
):
    user = UserRepository(db).get_by_id(request.user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    conversation_id = request.conversation_id or uuid4().hex

    graph = create_assistant_graph(
        model=model,
        tools=[*create_assistant_tools(db, user.id, embedder), *external_tools],
        checkpointer=memory,
        system_prompt=build_system_prompt(clock.today(), user.name),
        fallback_model=fallback_model,
    )
    config = {
        **_thread_config(user.id, conversation_id),
        "recursion_limit": RECURSION_LIMIT,
    }

    try:
        result = graph.invoke(
            {"messages": [HumanMessage(request.message)]},
            config=config,
        )
        reply = result["messages"][-1].text
        messages = result["messages"]
    except Exception as e:
        logger.exception("Assistant turn failed")

        # Tools may have changed bookings before the model failed. Never
        # report "unavailable" when something was actually done.
        messages = graph.get_state(config).values.get("messages", [])
        last_human = max(
            (i for i, m in enumerate(messages) if isinstance(m, HumanMessage)),
            default=None,
        )
        actions = _actions_in(messages[last_human + 1:]) if last_human is not None else []
        if not any(a.succeeded and a.tool in MUTATING_TOOLS for a in actions):
            raise HTTPException(
                status_code=503,
                detail="Clear Path's assistant is unavailable right now.",
            ) from e

        reply = (
            "I made changes to your bookings but couldn't finish replying. "
            "Check your rides to see the latest."
        )

    last_human = max(
        i for i, m in enumerate(messages) if isinstance(m, HumanMessage)
    )
    turn = messages[last_human + 1:]
    actions = _actions_in(turn, _tool_servers(external_tools))

    return AssistantMessageResponse(
        conversation_id=conversation_id,
        reply=reply,
        actions=actions,
        bookings_changed=any(
            a.succeeded and a.tool in MUTATING_TOOLS for a in actions
        ),
        sources=_sources_in(turn),
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
)
def get_conversation(
    conversation_id: str,
    user_id: int = Query(default=1, gt=0),
    memory: BaseCheckpointSaver = Depends(get_conversation_memory),
    external_tools: list[BaseTool] = Depends(get_external_tools),
):
    """Replay a conversation, e.g. to show Siri requests in the app chat."""

    checkpoint = memory.get(_thread_config(user_id, conversation_id))

    if checkpoint is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    stored = checkpoint["channel_values"].get("messages", [])
    human_indexes = [
        i for i, m in enumerate(stored) if isinstance(m, HumanMessage)
    ]

    messages = []
    for position, start in enumerate(human_indexes):
        end = (
            human_indexes[position + 1]
            if position + 1 < len(human_indexes)
            else len(stored)
        )
        turn = stored[start + 1:end]
        replies = [
            m for m in turn
            if isinstance(m, AIMessage) and not m.tool_calls and m.text
        ]

        messages.append(ConversationMessage(role="user", text=stored[start].text))
        if replies:
            messages.append(
                ConversationMessage(
                    role="assistant",
                    text=replies[-1].text,
                    actions=_actions_in(turn, _tool_servers(external_tools)),
                    sources=_sources_in(turn),
                )
            )

    return ConversationResponse(
        conversation_id=conversation_id,
        messages=messages,
    )
