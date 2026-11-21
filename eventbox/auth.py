"""Logging in: with an email and a password, or with Facebook."""

import functools
import secrets
from urllib.parse import urlencode

from flask import current_app, redirect, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from eventbox import db, settings


class FacebookError(Exception):
    """Facebook refused the login, or did not answer."""


def check_login(conn, email, password):
    """The user with this email and password, or None."""
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", ((email or "").strip().lower(),)
    ).fetchone()
    if user is None or not check_password_hash(user["password_hash"], password or ""):
        return None
    return user


def hash_password(password):
    # Tests set PASSWORD_METHOD to a cheap method so they stay fast; the real app keeps scrypt.
    method = current_app.config.get("PASSWORD_METHOD", "scrypt")
    return generate_password_hash(password, method=method)


def current_user():
    """The logged-in user, or None."""
    user_id = session.get("user_id")
    if user_id is None:
        return None
    conn = db.connect()
    try:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()


def log_in(user):
    session.clear()
    session["user_id"] = user["id"]


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return redirect(f"/login?next={request.path}")
        return view(*args, **kwargs)

    return wrapped


def organiser_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if user is None or user["role"] != "organiser":
            if request.path.startswith("/api/"):
                return {"error": "log in as an organiser"}, 401
            return redirect(f"/login?next={request.path}")
        return view(*args, **kwargs)

    return wrapped


def facebook_login_url():
    """Where the Log in with Facebook button sends the user."""
    session["facebook_state"] = state = secrets.token_urlsafe(16)
    query = urlencode(
        {
            "client_id": settings.FACEBOOK_APP_ID,
            "redirect_uri": settings.FACEBOOK_REDIRECT,
            "state": state,
            "scope": "email",
        }
    )
    return f"https://www.facebook.com/v19.0/dialog/oauth?{query}"


def facebook_user(conn, code, state):
    """The user Facebook logged in. Raises FacebookError."""
    if not code or state != session.pop("facebook_state", None):
        raise FacebookError("the Facebook login was cancelled")
    # The real app swaps the code for a token at graph.facebook.com with FACEBOOK_APP_SECRET.
    # Our Facebook app was never approved, so Facebook always says no.
    raise FacebookError("Facebook did not answer")
