"""How times are shown. Events are stored in UTC ("2026-12-03 17:00"): the database and the API
speak UTC, people read times on pages and in emails."""

from datetime import datetime, timezone

UTC = timezone.utc


def parse(text):
    """An event's stored start ("2026-12-03 17:00", UTC) as a datetime."""
    return datetime.strptime(text, "%Y-%m-%d %H:%M")


def show(text):
    """How pages and emails show an event's start: "Thu 3 Dec 2026, 20:00"."""
    when = parse(text)
    return f"{when:%a} {when.day} {when:%b %Y, %H:%M}"


def iso(text):
    """The API's form of an event's start: "2026-12-03T17:00:00Z" (UTC)."""
    return parse(text).strftime("%Y-%m-%dT%H:%M:00Z")
