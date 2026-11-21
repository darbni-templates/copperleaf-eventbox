from conftest import log_in


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Events in Bahrain" in response.text


def test_the_events_list(client):
    text = client.get("/events").text
    assert "Bahrain Jazz Night" in text
    assert "Sold out" in text  # the Pearl Diving Talk


def test_an_event_page(client):
    text = client.get("/events/1").text
    assert "Bahrain Jazz Night" in text
    assert "15.000 BHD" in text


def test_an_unknown_event_is_404(client):
    assert client.get("/events/999").status_code == 404


def test_logging_in_opens_the_account(client):
    response = log_in(client)
    assert response.headers["Location"] == "/account"
    assert "Hello, Fatima Ali" in client.get("/account").text


def test_a_wrong_password(client):
    assert log_in(client, password="nope").status_code == 401


def test_the_organiser_page_needs_an_organiser(client):
    log_in(client)
    assert client.get("/organiser").status_code == 302
