"""Orders: buying tickets for an event, as a guest or logged in."""

import re

from eventbox import catalog, clock, emails, inventory, pricing, qr

MAX_PER_ORDER = 10
CODE = re.compile(r"EB-(\d{4,})")


class OrderError(Exception):
    """An order we refuse: the HTTP status and the message for the buyer."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def code_of(order):
    """The code buyers see: EB- and 1000 + the order's id (EB-1015, ...)."""
    return f"EB-{1000 + order['id']}"


def find_order(conn, code):
    """The order with this code, or None."""
    match = CODE.fullmatch(code or "")
    if match is None:
        return None
    return conn.execute("SELECT * FROM orders WHERE id = ?", (int(match[1]) - 1000,)).fetchone()


def read_quantity(value):
    """The number of tickets asked for. Raises OrderError."""
    text = (
        str(value).strip() if isinstance(value, int | str) and not isinstance(value, bool) else ""
    )
    if not text.isdigit() or int(text) < 1:
        raise OrderError(400, "quantity must be a whole number of 1 or more")
    quantity = int(text)
    if quantity > MAX_PER_ORDER:
        raise OrderError(400, f"at most {MAX_PER_ORDER} tickets per order")
    return quantity


def place_order(conn, event_id, data, user=None):
    """Sells tickets. data: email, quantity and (optional) category. Returns the order row.
    Raises OrderError."""
    event = catalog.find_event(conn, event_id)
    if event is None:
        raise OrderError(404, "event not found")
    email = (data.get("email") or (user["email"] if user else "") or "").strip()
    if "@" not in email:
        raise OrderError(400, "missing email")
    quantity = read_quantity(data.get("quantity"))
    choice = {"category": (data.get("category") or "regular").strip().lower()}
    try:
        total = pricing.order_total(conn, event, choice, quantity)
    except pricing.PriceError as exc:
        raise OrderError(400, str(exc)) from None
    try:
        with inventory.reservation(conn, event, quantity):
            cursor = conn.execute(
                "INSERT INTO orders (event_id, user_id, email, quantity, total_fils, status,"
                " created_at) VALUES (?, ?, ?, ?, ?, 'paid', ?)",
                (
                    event["id"],
                    user["id"] if user else None,
                    email,
                    quantity,
                    total,
                    clock.now().isoformat(timespec="minutes"),
                ),
            )
            tokens = [qr.issue(conn, cursor.lastrowid, event["id"]) for _ in range(quantity)]
            order = conn.execute(
                "SELECT * FROM orders WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
            # In the same transaction: an order and its email are saved together, or not at all.
            emails.send_confirmation(conn, order, event, tokens)
    except inventory.SoldOut as exc:
        raise OrderError(409, str(exc)) from None
    return order


def tickets_of(conn, order):
    """The QR codes of an order's tickets, in order."""
    rows = conn.execute("SELECT qr FROM tickets WHERE order_id = ? ORDER BY id", (order["id"],))
    return [row["qr"] for row in rows]


def order_json(conn, order):
    return {
        "code": code_of(order),
        "event": order["event_id"],
        "email": order["email"],
        "quantity": order["quantity"],
        "total_fils": order["total_fils"],
        "status": order["status"],
        "tickets": tickets_of(conn, order),
    }
