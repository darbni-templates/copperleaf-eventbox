def buy(client, event=1, quantity=2, **more):
    body = {"email": "sara@example.com", "quantity": quantity, **more}
    return client.post(f"/api/events/{event}/orders", json=body)


def test_buying_two(client):
    response = buy(client)
    assert response.status_code == 201
    assert response.json["code"] == "EB-1015"
    assert response.json["total_fils"] == 30000
    assert len(response.json["tickets"]) == 2


def test_an_order_lowers_what_is_left(client):
    before = client.get("/api/events/1").json["left"]
    buy(client, quantity=3)
    assert client.get("/api/events/1").json["left"] == before - 3


def test_the_order_page_and_its_email(client):
    buy(client)
    assert "Order EB-1015" in client.get("/orders/EB-1015").text
    assert "Bahrain Jazz Night" in client.get("/orders/EB-1015/email").text


def test_an_order_needs_an_email(client):
    response = client.post("/api/events/1/orders", json={"quantity": 1})
    assert response.status_code == 400


def test_the_form_on_the_event_page(client):
    form = {"email": "sara@example.com", "quantity": "1"}
    response = client.post("/events/2/buy", data=form, follow_redirects=True)
    assert "Order EB-1015" in response.text


def test_a_ticket_can_be_verified(client):
    token = buy(client).json["tickets"][0]
    assert client.post("/api/tickets/verify", json={"token": token}).json["valid"] is True
