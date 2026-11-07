"""Simulated cloud-LLM outage for the F13 reliability demo.

While the flag file exists, every Gemini model the backend would create is
replaced by one that fails immediately, so the real failure paths run: the
agent tries each fallback model, gives up, and answers 503. Everything that
never needs the LLM (structured bookings, habits, tracking, schedule import)
keeps working.

The flag is a file, not a setting, so `python -m scripts.llm_outage on|off`
flips it while uvicorn runs: models are created per request, and each
creation checks the file. Deliberately not exposed over HTTP.

This module imports nothing from app.core.config or app.db, so the script
can run without a database or API key.
"""

from pathlib import Path

FLAG_PATH = Path(__file__).resolve().parents[2] / ".llm_outage"


def is_llm_outage() -> bool:
    return FLAG_PATH.exists()


def set_llm_outage(on: bool) -> None:
    if on:
        FLAG_PATH.write_text("Simulated LLM outage (python -m scripts.llm_outage off to end it).\n")
    else:
        FLAG_PATH.unlink(missing_ok=True)
