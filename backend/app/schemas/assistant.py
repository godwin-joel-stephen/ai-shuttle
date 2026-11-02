from pydantic import BaseModel, Field


class AssistantMessageRequest(BaseModel):
    user_id: int = Field(gt=0)
    message: str = Field(min_length=1, max_length=1000)
    # Omit to start a new conversation; send back the returned id to
    # continue it.
    conversation_id: str | None = Field(default=None, max_length=64)


class AssistantAction(BaseModel):
    """One tool call the agent made, for showing the agent's work."""

    tool: str
    arguments: dict
    succeeded: bool
    error: str | None = None


class AssistantMessageResponse(BaseModel):
    conversation_id: str
    reply: str
    actions: list[AssistantAction]
    bookings_changed: bool
    # Policy sections retrieved for this reply, e.g.
    # "Booking Policy › Service days".
    sources: list[str] = []


class ConversationMessage(BaseModel):
    role: str  # "user" or "assistant"
    text: str
    actions: list[AssistantAction] = []
    sources: list[str] = []


class ConversationResponse(BaseModel):
    conversation_id: str
    messages: list[ConversationMessage]
