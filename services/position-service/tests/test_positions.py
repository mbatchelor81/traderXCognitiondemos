"""Endpoint tests for position queries, apply and recalculation."""
from tests.conftest import TEST_TENANT_ID


def test_list_all_positions_empty(client):
    response = client.get("/positions/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_all_positions(client, seeded_positions):
    response = client.get("/positions/")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {p["security"] for p in body} == {"AAPL", "JPM"}
    assert all(p["tenant_id"] == TEST_TENANT_ID for p in body)


def test_list_positions_by_account(client, seeded_positions):
    response = client.get("/positions/22214")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0] == {
        "accountId": 22214,
        "tenant_id": TEST_TENANT_ID,
        "security": "AAPL",
        "quantity": 70,
        "updated": body[0]["updated"],
    }


def test_list_positions_for_unknown_account_is_empty(client, seeded_positions):
    response = client.get("/positions/99999")
    assert response.status_code == 200
    assert response.json() == []


def test_list_positions_rejects_non_integer_account(client):
    response = client.get("/positions/not-a-number")
    assert response.status_code == 422


def test_apply_creates_missing_position(client):
    response = client.post("/positions/apply", json={
        "accountId": 22214, "security": "MSFT", "quantityDelta": 250,
    })
    assert response.status_code == 200
    body = response.json()
    assert body["accountId"] == 22214
    assert body["security"] == "MSFT"
    assert body["quantity"] == 250
    assert body["tenant_id"] == TEST_TENANT_ID
    assert body["updated"] is not None


def test_apply_accumulates_delta(client, seeded_positions):
    client.post("/positions/apply", json={
        "accountId": 22214, "security": "AAPL", "quantityDelta": 30,
    })
    response = client.post("/positions/apply", json={
        "accountId": 22214, "security": "AAPL", "quantityDelta": -50,
    })
    assert response.status_code == 200
    assert response.json()["quantity"] == 50

    listed = client.get("/positions/22214").json()
    assert [p["quantity"] for p in listed] == [50]


def test_apply_allows_negative_resulting_quantity(client):
    response = client.post("/positions/apply", json={
        "accountId": 1, "security": "TSLA", "quantityDelta": -75,
    })
    assert response.status_code == 200
    assert response.json()["quantity"] == -75


def test_apply_rejects_missing_fields(client):
    response = client.post("/positions/apply", json={"accountId": 1})
    assert response.status_code == 422


def test_apply_rejects_empty_security(client):
    response = client.post("/positions/apply", json={
        "accountId": 1, "security": "", "quantityDelta": 5,
    })
    assert response.status_code == 422


def test_recalculate_sets_net_quantities(client, seeded_positions):
    response = client.post("/positions/recalculate", json={
        "accountId": 22214,
        "trades": [
            {"security": "AAPL", "side": "Buy", "quantity": 100},
            {"security": "AAPL", "side": "Sell", "quantity": 30},
            {"security": "MSFT", "side": "Buy", "quantity": 250},
        ],
    })
    assert response.status_code == 200
    by_security = {p["security"]: p["quantity"] for p in response.json()}
    assert by_security == {"AAPL": 70, "MSFT": 250}

    stored = {p["security"]: p["quantity"] for p in client.get("/positions/22214").json()}
    assert stored == {"AAPL": 70, "MSFT": 250}


def test_recalculate_overwrites_rather_than_accumulates(client, seeded_positions):
    client.post("/positions/recalculate", json={
        "accountId": 22214,
        "trades": [{"security": "AAPL", "side": "Buy", "quantity": 10}],
    })
    response = client.post("/positions/recalculate", json={
        "accountId": 22214,
        "trades": [{"security": "AAPL", "side": "Buy", "quantity": 10}],
    })
    assert [p["quantity"] for p in response.json()] == [10]


def test_recalculate_leaves_untouched_securities_alone(client, seeded_positions):
    client.post("/positions/recalculate", json={
        "accountId": 22214,
        "trades": [{"security": "MSFT", "side": "Buy", "quantity": 5}],
    })
    stored = {p["security"]: p["quantity"] for p in client.get("/positions/22214").json()}
    assert stored == {"AAPL": 70, "MSFT": 5}


def test_recalculate_with_no_trades_returns_empty(client, seeded_positions):
    response = client.post("/positions/recalculate", json={
        "accountId": 22214, "trades": [],
    })
    assert response.status_code == 200
    assert response.json() == []


def test_recalculate_rejects_missing_account(client):
    response = client.post("/positions/recalculate", json={"trades": []})
    assert response.status_code == 422


def test_recalculate_rejects_malformed_trade(client):
    response = client.post("/positions/recalculate", json={
        "accountId": 1, "trades": [{"security": "AAPL", "side": "Buy"}],
    })
    assert response.status_code == 422
