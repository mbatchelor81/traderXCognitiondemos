"""Tests for Position Service."""


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["service"] == "position-service"
    assert data["tenant"] == "test_tenant"


def test_list_positions_empty(client):
    response = client.get("/positions/")
    assert response.status_code == 200
    assert response.json() == []


def test_update_position_buy(client):
    response = client.post("/positions/update", json={
        "accountId": 1001, "security": "AAPL", "side": "Buy",
        "quantity": 100, "tenant_id": "test_tenant",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["accountId"] == 1001
    assert data["security"] == "AAPL"
    assert data["quantity"] == 100


def test_update_position_sell(client):
    # Buy first
    client.post("/positions/update", json={
        "accountId": 1001, "security": "AAPL", "side": "Buy",
        "quantity": 100, "tenant_id": "test_tenant",
    })
    # Then sell
    response = client.post("/positions/update", json={
        "accountId": 1001, "security": "AAPL", "side": "Sell",
        "quantity": 30, "tenant_id": "test_tenant",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == 70


def test_list_positions_by_account(client):
    client.post("/positions/update", json={
        "accountId": 2001, "security": "MSFT", "side": "Buy",
        "quantity": 50, "tenant_id": "test_tenant",
    })
    response = client.get("/positions/2001")
    assert response.status_code == 200
    positions = response.json()
    assert len(positions) == 1
    assert positions[0]["security"] == "MSFT"
