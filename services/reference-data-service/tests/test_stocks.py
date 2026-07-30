"""Stock lookup and search endpoints."""


def test_list_all_stocks_returns_full_catalogue(client):
    response = client.get("/stocks/")
    assert response.status_code == 200
    stocks = response.json()
    assert len(stocks) > 400
    assert {"ticker", "companyName"} == set(stocks[0])
    assert any(stock["ticker"] == "AAPL" for stock in stocks)


def test_search_filters_by_ticker_and_company_name(client):
    by_ticker = client.get("/stocks/", params={"search": "aapl"}).json()
    assert [stock["ticker"] for stock in by_ticker] == ["AAPL"]

    by_name = client.get("/stocks/", params={"search": "apple"}).json()
    assert any(stock["companyName"] == "Apple" for stock in by_name)


def test_search_with_no_matches_returns_empty_list(client):
    assert client.get("/stocks/", params={"search": "zzzznotareal"}).json() == []


def test_limit_truncates_results(client):
    stocks = client.get("/stocks/", params={"limit": 5}).json()
    assert len(stocks) == 5


def test_limit_must_be_positive(client):
    assert client.get("/stocks/", params={"limit": 0}).status_code == 422


def test_get_stock_by_ticker(client):
    response = client.get("/stocks/AAPL")
    assert response.status_code == 200
    assert response.json() == {"ticker": "AAPL", "companyName": "Apple"}


def test_get_stock_by_unknown_ticker_returns_404(client):
    response = client.get("/stocks/NOTATICKER")
    assert response.status_code == 404
    assert response.json()["detail"] == 'Stock ticker "NOTATICKER" not found.'


def test_ticker_lookup_is_case_sensitive_like_the_monolith(client):
    assert client.get("/stocks/aapl").status_code == 404
