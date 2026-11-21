"""The app's settings. On the server the secrets come from environment variables; the defaults
are for your laptop only."""

import os

SECRET_KEY = os.environ.get("EVENTBOX_SECRET_KEY", "dev-only-change-me")
# The door staff's scanners send this key with every check-in.
DOOR_KEY = os.environ.get("EVENTBOX_DOOR_KEY", "dev-door-key")

# Log in with Facebook (added at launch).
FACEBOOK_APP_ID = os.environ.get("FACEBOOK_APP_ID", "1234567890")
FACEBOOK_APP_SECRET = os.environ.get("FACEBOOK_APP_SECRET", "dev-facebook-secret")
FACEBOOK_REDIRECT = "http://127.0.0.1:5000/login/facebook/callback"
