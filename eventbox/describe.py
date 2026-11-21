"""The AI that writes an event's description for its page."""

from eventbox import ai


def write_description(conn, event, notes):
    """Asks the AI for a description, saves it and returns {"description": ..., "ai": True}."""
    prompt = (
        f"Write a short description for the event {event['name']} at {event['venue']}. "
        f"The organiser's notes: {notes}"
    )
    text = ai.ask_llm(prompt).strip()
    conn.execute("UPDATE events SET description = ? WHERE id = ?", (text, event["id"]))
    conn.commit()
    return {"description": text, "ai": True}
