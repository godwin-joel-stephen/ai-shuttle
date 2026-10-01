from datetime import date
from enum import StrEnum

from pydantic import BaseModel


class AgentIntent(StrEnum):
    BOOK_USUAL_SHUTTLE = "book_usual_shuttle"


class AgentRequest(BaseModel):
    intent: AgentIntent
    booking_date: date
