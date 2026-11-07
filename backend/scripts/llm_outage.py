"""Simulate the cloud LLM going down, live, for the F13 reliability demo.

    python -m scripts.llm_outage on       # every Gemini call fails at once
    python -m scripts.llm_outage off      # back to normal
    python -m scripts.llm_outage          # show the current state

No uvicorn restart needed: the backend checks the flag on every request.
While it's on, the chat and "Ask Clear Path" answer 503 with an honest
message; Siri "Book my usual shuttle", the widget, Control Center, the
Siri card Earlier/Later, tracking, habits and schedule import keep working.
"""

import argparse

from app.core.outage import FLAG_PATH, is_llm_outage, set_llm_outage


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("state", nargs="?", choices=["on", "off"])
    args = parser.parse_args()

    if args.state is not None:
        set_llm_outage(args.state == "on")

    if is_llm_outage():
        print(f"LLM outage ON ({FLAG_PATH}). The assistant answers 503; bookings still work.")
    else:
        print("LLM outage off. The assistant uses Gemini as usual.")


if __name__ == "__main__":
    main()
