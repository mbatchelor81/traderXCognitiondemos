"""Catalogue loading, immutability, and startup configuration."""

import os
import subprocess
import sys

import pytest

from app.services import stocks_service

SERVICE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_catalogue_is_resolved_relative_to_the_service_package(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    stocks = stocks_service.load_catalogue()
    assert len(stocks) > 400


def test_catalogue_entries_are_immutable():
    stocks_service.load_catalogue()
    stock = stocks_service.list_stocks("test_tenant", limit=1)
    # Callers get plain dict copies; mutating one must not affect the catalogue.
    stock[0]["ticker"] = "MUTATED"
    assert stocks_service.list_stocks("test_tenant", limit=1)[0]["ticker"] != "MUTATED"


def test_missing_csv_yields_an_empty_catalogue(tmp_path):
    try:
        stocks = stocks_service.load_catalogue(str(tmp_path / "missing.csv"))
        assert stocks == ()
        assert stocks_service.find_stock_by_ticker("test_tenant", "AAPL") is None
    finally:
        stocks_service.load_catalogue()


def test_startup_fails_without_tenant_id():
    env = {k: v for k, v in os.environ.items() if k != "TENANT_ID"}
    result = subprocess.run(
        [sys.executable, "-c", "import app.config"],
        cwd=SERVICE_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode != 0
    assert "TENANT_ID environment variable is required" in result.stderr


@pytest.mark.parametrize("ticker", ["AAPL", "MSFT"])
def test_known_tickers_resolve(ticker):
    stocks_service.load_catalogue()
    assert stocks_service.find_stock_by_ticker("test_tenant", ticker) is not None
