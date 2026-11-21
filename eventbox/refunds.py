"""Refunds."""


class RefundError(Exception):
    """A refund we refuse: the HTTP status and the message for the buyer."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def refund(conn, order):
    """Refunds an order. Returns the refunded amount in fils. Raises RefundError.

    Never built: the support team refunds by hand."""
    raise RefundError(409, "refunds by email only: write to help@eventbox.example")
