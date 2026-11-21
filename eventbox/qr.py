"""The codes in the tickets' QR codes. The door staff scan them."""


def next_number(conn, event_id):
    """The next ticket number of the event: 1, 2, 3, ..."""
    count = conn.execute("SELECT COUNT(*) FROM tickets WHERE event_id = ?", (event_id,)).fetchone()
    return count[0] + 1


def issue(conn, order_id, event_id):
    """Makes one ticket of an order and returns its QR code, like T005-0029."""
    token = f"T{event_id:03d}-{next_number(conn, event_id):04d}"
    conn.execute(
        "INSERT INTO tickets (order_id, event_id, qr) VALUES (?, ?, ?)", (order_id, event_id, token)
    )
    return token


def find_ticket(conn, token):
    """The ticket with this QR code, or None."""
    if not isinstance(token, str) or not token:
        return None
    return conn.execute("SELECT * FROM tickets WHERE qr = ?", (token,)).fetchone()
