"""Ticket prices. A buyer's choice is a dict of what they picked on the form or in the API."""


class PriceError(Exception):
    """A choice we can't sell. str(error) is the message for the buyer."""


def price_list(conn, event):
    """[(name, price in fils), ...]: the prices the event page shows."""
    return [("Regular", event["price_fils"])]


def unit_price(conn, event, choice):
    """The price of one ticket, in fils."""
    return event["price_fils"]


def order_total(conn, event, choice, quantity):
    """What an order costs, in fils."""
    return unit_price(conn, event, choice) * quantity
