"""The one place the app talks to an AI model.

Always call it as:

    from eventbox import ai
    reply = ai.ask_llm(prompt)

No real model is set up yet, so on your machine ask_llm returns a demo reply. Set the
environment variable EVENTBOX_AI=fail to make it raise RuntimeError instead, like a real
model that is down: every feature that uses AI needs a fallback for that.
Darbni's tests replace ask_llm with a fake model.
"""

import os


def ask_llm(prompt: str) -> str:
    if os.environ.get("EVENTBOX_AI") == "fail":
        raise RuntimeError("The AI is down (EVENTBOX_AI=fail)")
    return "An evening to remember, with the best seats in town."
