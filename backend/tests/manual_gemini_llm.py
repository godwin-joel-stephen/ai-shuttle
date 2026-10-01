from datetime import date

from app.agent.gemini_llm import GeminiLLM
from app.agent.schemas import AgentIntent
from app.core.config import settings


def main() -> None:
    llm = GeminiLLM(
        api_key=settings.gemini_api_key,
        reference_date=date(2026, 10, 1),
    )

    result = llm.invoke("Book my usual shuttle for tomorrow.")

    print("Intent:", result.intent)
    print("Booking date:", result.booking_date)

    assert result.intent == AgentIntent.BOOK_USUAL_SHUTTLE
    assert result.booking_date == date(2026, 10, 2)


if __name__ == "__main__":
    main()