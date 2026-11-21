"""The emails EventBox sends. They are saved in the outbox table; the mail server sends them."""

from eventbox import clock, timeutil


def confirmation(order, event, tokens):
    """(subject, body) of the email a buyer gets after an order."""
    subject = f"Your EventBox tickets for {event['name']}"
    lines = [
        "Hello,",
        "",
        f"Here are your {len(tokens)} tickets for {event['name']}, "
        f"{timeutil.show(event['starts_at'])}, at {event['venue']}.",
        "",
        *(f"Ticket {number}: {token}" for number, token in enumerate(tokens, 1)),
        "",
        "Show each QR code at the door. See you there!",
        "EventBox",
    ]
    return subject, "\n".join(lines)


def send_confirmation(conn, order, event, tokens):
    """Puts the confirmation email in the outbox. The caller commits, with the order."""
    subject, body = confirmation(order, event, tokens)
    conn.execute(
        "INSERT INTO outbox (to_email, subject, body, created_at) VALUES (?, ?, ?, ?)",
        (order["email"], subject, body, clock.now().isoformat(timespec="minutes")),
    )


def latest_to(conn, email):
    """The newest email sent to this address, or None."""
    return conn.execute(
        "SELECT * FROM outbox WHERE to_email = ? ORDER BY id DESC LIMIT 1", (email,)
    ).fetchone()
