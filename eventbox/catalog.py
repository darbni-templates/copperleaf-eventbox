"""The events: the list of upcoming events and the details of one."""

from eventbox import clock, inventory, pricing, timeutil


def find_event(conn, event_id):
    """The event with this id, or None."""
    return conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()


def now_utc():
    """Now, written like the events' starts ("2026-12-03 17:00", UTC)."""
    return clock.now().astimezone(timeutil.UTC).strftime("%Y-%m-%d %H:%M")


def as_card(conn, event):
    """What a list shows of an event."""
    return {
        "id": event["id"],
        "name": event["name"],
        "venue": event["venue"],
        "when": timeutil.show(event["starts_at"]),
        "starts_at": timeutil.iso(event["starts_at"]),
        "price_fils": event["price_fils"],
        "left": inventory.tickets_left(conn, event),
    }


def list_events(conn):
    """Every event that has not started yet, soonest first."""
    events = conn.execute(
        "SELECT * FROM events WHERE starts_at > ? ORDER BY starts_at, id", (now_utc(),)
    ).fetchall()
    return [as_card(conn, event) for event in events]


def event_details(conn, event_id):
    """Everything the event page shows, or None for an unknown event."""
    event = find_event(conn, event_id)
    if event is None:
        return None
    return {
        **as_card(conn, event),
        "description": event["description"],
        "capacity": event["capacity"],
        "prices": pricing.price_list(conn, event),
    }
