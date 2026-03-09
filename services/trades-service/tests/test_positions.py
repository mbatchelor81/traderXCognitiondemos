"""Test position endpoints for trades-service."""
from unittest.mock import patch


def test_list_positions_empty(client):
    response = client.get("/positions/")
    assert response.status_code == 200
    assert response.json() == []


@patch("app.services.trade_processor.validate_account_exists", return_value=True)
def test_positions_update_after_trade(mock_validate, client):
    # Create a buy trade
    client.post("/trade/", json={
        "accountId": 22214,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100,
    })

    # Check positions
    response = client.get("/positions/22214")
    assert response.status_code == 200
    positions = response.json()
    assert len(positions) == 1
    assert positions[0]["quantity"] == 100

    # Create a sell trade for the same security
    client.post("/trade/", json={
        "accountId": 22214,
        "security": "AAPL",
        "side": "Sell",
        "quantity": 30,
    })

    # Check updated position
    response = client.get("/positions/22214")
    positions = response.json()
    assert len(positions) == 1
    assert positions[0]["quantity"] == 70
