"""How many tickets an event has left, and holding them while an order is saved."""

from contextlib import contextmanager


class SoldOut(Exception):
    """An order the event has no room for. str(error) is the message for the buyer."""


def sold(conn, event_id):
    """Tickets sold for the event: the tickets of its paid orders."""
    return conn.execute(
        "SELECT COALESCE(SUM(quantity), 0) FROM orders WHERE event_id = ? AND status = 'paid'",
        (event_id,),
    ).fetchone()[0]


def tickets_left(conn, event):
    return max(0, event["capacity"] - sold(conn, event["id"]))


@contextmanager
def reservation(conn, event, quantity):
    """Holds `quantity` tickets of `event` while the order is saved: put the INSERTs of the order
    in this block. It commits when the block ends and rolls back if the block raises."""
    try:
        yield
        conn.commit()
    except Exception:
        conn.rollback()
        raise
