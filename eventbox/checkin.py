"""Check-in at the door: the staff's scanners send each ticket's QR code."""


class CheckinError(Exception):
    """A scan we refuse: the HTTP status and the message for the door staff."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def check_in(conn, data, door_key):
    """Checks a ticket in. data: the scanner's door_key and the ticket's token. Returns the
    ticket row. Raises CheckinError.

    Never built: the door staff tick names off a printed list."""
    raise CheckinError(501, "check-in is not ready yet")
