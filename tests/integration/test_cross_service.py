#!/usr/bin/env python3
"""
Integration test script for cross-service communication.

Starts all 5 extracted services in the background, waits for /health endpoints,
runs end-to-end cross-service operations, and tears down.

Usage:
    TENANT_ID=test_tenant python tests/integration/test_cross_service.py
"""
import os
import sys
import time
import signal
import subprocess
import json

import httpx

TENANT_ID = os.environ.get("TENANT_ID", "integration_test")
os.environ["TENANT_ID"] = TENANT_ID

SERVICES = [
    {
        "name": "people-service",
        "dir": os.path.join(os.path.dirname(__file__), "..", "..", "services", "people-service"),
        "port": 8005,
        "cmd": [sys.executable, "run.py"],
    },
    {
        "name": "reference-data-service",
        "dir": os.path.join(os.path.dirname(__file__), "..", "..", "services", "reference-data-service"),
        "port": 8004,
        "cmd": [sys.executable, "run.py"],
    },
    {
        "name": "account-service",
        "dir": os.path.join(os.path.dirname(__file__), "..", "..", "services", "account-service"),
        "port": 8001,
        "cmd": [sys.executable, "run.py"],
    },
    {
        "name": "position-service",
        "dir": os.path.join(os.path.dirname(__file__), "..", "..", "services", "position-service"),
        "port": 8003,
        "cmd": [sys.executable, "run.py"],
    },
    {
        "name": "trading-service",
        "dir": os.path.join(os.path.dirname(__file__), "..", "..", "services", "trading-service"),
        "port": 8002,
        "cmd": [sys.executable, "run.py"],
    },
]

processes = []


def start_services():
    """Start all services in the background."""
    env = os.environ.copy()
    env["TENANT_ID"] = TENANT_ID
    for svc in SERVICES:
        print(f"Starting {svc['name']} on port {svc['port']}...")
        proc = subprocess.Popen(
            svc["cmd"],
            cwd=os.path.abspath(svc["dir"]),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        processes.append((svc["name"], proc))
    print(f"Started {len(processes)} services.")


def wait_for_health(max_wait=30):
    """Wait for all services to be healthy."""
    print("Waiting for all services to become healthy...")
    start = time.time()
    for svc in SERVICES:
        url = f"http://localhost:{svc['port']}/health"
        while time.time() - start < max_wait:
            try:
                resp = httpx.get(url, timeout=2.0)
                if resp.status_code == 200:
                    data = resp.json()
                    assert data["status"] == "UP", f"{svc['name']} health status != UP"
                    assert data["tenant"] == TENANT_ID, f"{svc['name']} tenant mismatch"
                    print(f"  {svc['name']} healthy: {data}")
                    break
            except (httpx.RequestError, AssertionError) as e:
                time.sleep(0.5)
        else:
            raise TimeoutError(f"{svc['name']} did not become healthy within {max_wait}s")
    print("All services healthy!")


def teardown():
    """Kill all background service processes."""
    print("Tearing down services...")
    for name, proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        print(f"  Stopped {name}")

    # Clean up any generated DB files
    for svc in SERVICES:
        db_file = os.path.join(os.path.abspath(svc["dir"]), f"app_{TENANT_ID}.db")
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"  Removed {db_file}")
    print("Teardown complete.")


def test_cross_service_trade_flow():
    """
    End-to-end test:
    1. Create an account via account-service
    2. Verify a stock exists via reference-data-service
    3. Submit a trade via trading-service (validates account + security via HTTP)
    4. Check positions via position-service (shared DB with trading-service for now)
    """
    print("\n=== Cross-Service Trade Flow Test ===\n")

    # 1. Create an account via account-service
    print("Step 1: Create account via account-service...")
    resp = httpx.post(
        "http://localhost:8001/account/",
        json={"displayName": "Integration Test Account"},
        timeout=5.0,
    )
    assert resp.status_code == 200, f"Failed to create account: {resp.status_code} {resp.text}"
    account = resp.json()
    account_id = account["id"]
    print(f"  Created account: id={account_id}, displayName={account['displayName']}")

    # 2. Verify a stock exists via reference-data-service
    print("Step 2: Verify stock AAPL via reference-data-service...")
    resp = httpx.get("http://localhost:8004/stocks/AAPL", timeout=5.0)
    assert resp.status_code == 200, f"Stock AAPL not found: {resp.status_code}"
    stock = resp.json()
    print(f"  Stock found: {stock['Symbol']} - {stock['CompanyName']}")

    # 3. Submit a trade via trading-service
    print("Step 3: Submit trade via trading-service...")
    resp = httpx.post(
        "http://localhost:8002/trade/",
        json={
            "accountId": account_id,
            "security": "AAPL",
            "side": "Buy",
            "quantity": 100,
        },
        timeout=10.0,
    )
    assert resp.status_code == 200, f"Failed to submit trade: {resp.status_code} {resp.text}"
    result = resp.json()
    assert result["success"] is True, f"Trade not successful: {result}"
    trade = result["trade"]
    position = result["position"]
    print(f"  Trade submitted: id={trade['id']}, state={trade['state']}")
    print(f"  Position updated: security={position['security']}, quantity={position['quantity']}")

    # 4. Verify trade appears in trade list
    print("Step 4: Verify trade in trading-service trade list...")
    resp = httpx.get(f"http://localhost:8002/trades/{account_id}", timeout=5.0)
    assert resp.status_code == 200
    trades = resp.json()
    assert len(trades) >= 1, "No trades found for account"
    print(f"  Found {len(trades)} trade(s) for account {account_id}")

    # 5. Verify a person lookup works via people-service
    print("Step 5: Verify person lookup via people-service...")
    resp = httpx.get(
        "http://localhost:8005/people/ValidatePerson",
        params={"LogonId": "jsmith"},
        timeout=5.0,
    )
    assert resp.status_code == 200
    person_valid = resp.json()
    print(f"  Person validation: {person_valid}")

    print("\n=== All Cross-Service Tests Passed! ===\n")


def main():
    try:
        start_services()
        wait_for_health()
        test_cross_service_trade_flow()
        print("INTEGRATION TEST: PASSED")
        return 0
    except Exception as e:
        print(f"\nINTEGRATION TEST: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        teardown()


if __name__ == "__main__":
    sys.exit(main())
