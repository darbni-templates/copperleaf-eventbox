import pytest

from eventbox import create_app


@pytest.fixture
def app(tmp_path):
    # NOW fixes EventBox's clock (clock.now()): Tuesday 17 November 2026, 10:00 in Bahrain.
    # PASSWORD_METHOD: a cheap hash, so sign-up tests stay fast.
    return create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "test.sqlite"),
            "NOW": "2026-11-17T10:00",
            "PASSWORD_METHOD": "pbkdf2:sha256:1000",
        }
    )


@pytest.fixture
def client(app):
    return app.test_client()


def log_in(client, email="fatima@example.com", password="events123"):
    return client.post("/login", data={"email": email, "password": password})
