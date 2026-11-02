from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class ScriptedChatModel(BaseChatModel):
    """Deterministic stand-in for Gemini: replays scripted replies.

    Each script step is an AIMessage, or a callable that receives the
    messages the model was given (to make assertions or build the reply
    from earlier tool results).
    """

    # AIMessage or Callable[[list[BaseMessage]], AIMessage]; typed Any so
    # pydantic does not try to coerce callables into messages.
    script: list[Any]
    received: list[list[BaseMessage]] = []

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools: Any, **kwargs: Any) -> "ScriptedChatModel":
        return self

    def _generate(self, messages: list[BaseMessage], *args: Any, **kwargs: Any) -> ChatResult:
        self.received.append(list(messages))
        step = self.script.pop(0)
        reply = step(messages) if callable(step) else step
        return ChatResult(generations=[ChatGeneration(message=reply)])


def call(name: str, call_id: str = "call-1", **args: Any) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[{"name": name, "args": args, "id": call_id}],
    )
