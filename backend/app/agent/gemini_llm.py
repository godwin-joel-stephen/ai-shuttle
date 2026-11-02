from datetime import date

from google import genai
from google.genai import types

from app.agent.schemas import AgentRequest


class GeminiLLM:
    """Gemini-backed implementation of the application LLM interface."""

    MODEL = "gemini-3.1-flash-lite"
    TIMEOUT_MS = 10_000  # Gemini rejects deadlines below 10s

    def __init__(self, api_key: str, reference_date: date):
        # Fail fast: a hung model call would outlast Siri's patience.
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=self.TIMEOUT_MS),
        )
        self.reference_date = reference_date

    def invoke(self, user_input: str) -> AgentRequest:
        prompt = f"""
You are the AI Shuttle request interpreter.

Today is {self.reference_date.isoformat()}.

Interpret the user's request and return only the structured data
required by the provided schema.

Rules:
- Only identify the user's intent and booking date.
- Do not access databases.
- Do not check shuttle availability.
- Do not create or modify bookings.
- Do not invent shuttle information.
- For "tomorrow", use the date immediately after today.
- The supported intent is: book_usual_shuttle.

User request:
{user_input}
""".strip()

        response = self.client.models.generate_content(
            model=self.MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AgentRequest,
            ),
        )

        if response.parsed is None:
            raise ValueError("Gemini returned no structured agent request.")

        return response.parsed