"""
Integration test for cross-service communication.

Starts users-service and trades-service in the background with TENANT_ID=acme_corp,
waits for health endpoints, runs cross-service operations, and tears down.

Usage:
    TENANT_ID=acme_corp python tests/integration/test_cross_service.py
"""

import os
import sys
import time
import signal
import subprocess
import json

import httpx

TENANT_ID = os.environ.get("TENANT_ID", "acme_corp")
USERS_SERVICE_URL = "http://localhost:8001"
TRADES_SERVICE_URL = "http://localhost:8002"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

processes = []


def start_service(name: str, service_dir: str, port: int):
    """Start a service in the background."""
    env = os.environ.copy()
    env["TENANT_ID"] = TENANT_ID
    env["DATABASE_URL"] = f"sqlite:///app_integration_{TENANT_ID}.db"

    proc = subprocess.Popen(
        [sys.executable, "run.py"],
        cwd=service_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    processes.append((name, proc, service_dir))
    print(f"  Started {name} (PID {proc.pid}) on port {port}")
    return proc


def wait_for_health(url: str, name: str, timeout: int = 30):
    """Wait for a service's /health endpoint to respond."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = httpx.get(f"{url}/health", timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                print(f"  {name} healthy: {json.dumps(data)}")
                return True
        except (httpx.RequestError, httpx.TimeoutException):
            pass
        time.sleep(1)

    print(f"  ERROR: {name} did not become healthy within {timeout}s")
    return False


def teardown():
    """Kill all background service processes and clean up."""
    print("\n--- Teardown ---")
    for name, proc, service_dir in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
            print(f"  Stopped {name} (PID {proc.pid})")
        except subprocess.TimeoutExpired:
            proc.kill()
            print(f"  Force-killed {name} (PID {proc.pid})")

    # Clean up integration database files
    for name, proc, service_dir in processes:
        db_file = os.path.join(service_dir, f"app_integration_{TENANT_ID}.db")
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"  Cleaned up {db_file}")


def test_cross_service_trade_with_account_validation():
    """
    End-to-end test:
    1. Create an account in users-service
    2. Submit a trade in trades-service (which validates account via HTTP call to users-service)
    3. Assert the trade was created and position was updated
    """
    print("\n--- Test: Cross-service trade with account validation ---")

    # Step 1: Create an account in users-service
    print("  Step 1: Creating account in users-service...")
    resp = httpx.post(
        f"{USERS_SERVICE_URL}/account/",
        json={"id": 99901, "displayName": "Integration Test Account"},
        headers={"X-Tenant-ID": TENANT_ID},
        timeout=5.0,
    )
    assert resp.status_code == 200, f"Failed to create account: {resp.status_code} {resp.text}"
    account = resp.json()
    assert account["id"] == 99901
    print(f"  Account created: {json.dumps(account)}")

    # Step 2: Verify account exists via GET
    print("  Step 2: Verifying account exists...")
    resp = httpx.get(
        f"{USERS_SERVICE_URL}/account/99901",
        headers={"X-Tenant-ID": TENANT_ID},
        timeout=5.0,
    )
    assert resp.status_code == 200, f"Account not found: {resp.status_code}"
    print(f"  Account verified: {json.dumps(resp.json())}")

    # Step 3: Submit a trade in trades-service (validates account via users-service HTTP call)
    print("  Step 3: Submitting trade in trades-service...")
    resp = httpx.post(
        f"{TRADES_SERVICE_URL}/trade/",
        json={
            "accountId": 99901,
            "security": "AAPL",
            "side": "Buy",
            "quantity": 100,
        },
        headers={"X-Tenant-ID": TENANT_ID},
        timeout=10.0,
    )
    assert resp.status_code == 200, f"Failed to submit trade: {resp.status_code} {resp.text}"
    result = resp.json()
    assert result["success"] is True, f"Trade failed: {result.get('error')}"
    assert result["trade"]["accountId"] == 99901
    assert result["trade"]["security"] == "AAPL"
    assert result["trade"]["quantity"] == 100
    print(f"  Trade created: id={result['trade']['id']} state={result['trade']['state']}")

    # Step 4: Verify position was created
    print("  Step 4: Verifying position...")
    resp = httpx.get(
        f"{TRADES_SERVICE_URL}/positions/99901",
        headers={"X-Tenant-ID": TENANT_ID},
        timeout=5.0,
    )
    assert resp.status_code == 200
    positions = resp.json()
    assert len(positions) >= 1, "No positions found"
    aapl_pos = [p for p in positions if p["security"] == "AAPL"]
    assert len(aapl_pos) == 1, "AAPL position not found"
    assert aapl_pos[0]["quantity"] == 100
    print(f"  Position verified: {json.dumps(aapl_pos[0])}")

    print("  PASSED: Cross-service trade with account validation")


def test_cross_service_trade_with_invalid_account():
    """
    Test that trades-service rejects a trade when the account doesn't exist
    in users-service.
    """
    print("\n--- Test: Cross-service trade with invalid account ---")

    resp = httpx.post(
        f"{TRADES_SERVICE_URL}/trade/",
        json={
            "accountId": 88888,
            "security": "AAPL",
            "side": "Buy",
            "quantity": 50,
        },
        headers={"X-Tenant-ID": TENANT_ID},
        timeout=10.0,
    )
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
    print(f"  Trade correctly rejected: {resp.json().get('detail', '')}")

    print("  PASSED: Trade with invalid account correctly rejected")


def test_people_service():
    """Test that the people endpoints work in users-service."""
    print("\n--- Test: People service endpoints ---")

    # Search for people
    resp = httpx.get(
        f"{USERS_SERVICE_URL}/people/GetMatchingPeople?SearchText=john&Take=5",
        headers={"X-Tenant-ID": TENANT_ID},
        timeout=5.0,
    )
    assert resp.status_code == 200
    people = resp.json()
    print(f"  Found {len(people)} people matching 'john'")

    # Validate a person
    resp = httpx.get(
        f"{USERS_SERVICE_URL}/people/ValidatePerson?LogonId=jsmith",
        headers={"X-Tenant-ID": TENANT_ID},
        timeout=5.0,
    )
    assert resp.status_code == 200
    result = resp.json()
    print(f"  ValidatePerson(jsmith): {json.dumps(result)}")

    print("  PASSED: People service endpoints")


def test_reference_data():
    """Test that reference data (stocks) is available in trades-service."""
    print("\n--- Test: Reference data endpoints ---")

    resp = httpx.get(
        f"{TRADES_SERVICE_URL}/stocks/",
        headers={"X-Tenant-ID": TENANT_ID},
        timeout=5.0,
    )
    assert resp.status_code == 200
    stocks = resp.json()
    assert len(stocks) > 0
    print(f"  Found {len(stocks)} stocks in reference data")

    resp = httpx.get(
        f"{TRADES_SERVICE_URL}/stocks/AAPL",
        headers={"X-Tenant-ID": TENANT_ID},
        timeout=5.0,
    )
    assert resp.status_code == 200
    stock = resp.json()
    assert stock["ticker"] == "AAPL"
    print(f"  AAPL found: {json.dumps(stock)}")

    print("  PASSED: Reference data endpoints")


def main():
    """Run all integration tests."""
    print(f"=== Integration Tests (TENANT_ID={TENANT_ID}) ===\n")

    users_dir = os.path.join(REPO_ROOT, "services", "users-service")
    trades_dir = os.path.join(REPO_ROOT, "services", "trades-service")

    # Start services
    print("--- Starting services ---")
    start_service("users-service", users_dir, 8001)
    start_service("trades-service", trades_dir, 8002)

    try:
        # Wait for health
        print("\n--- Waiting for services to be healthy ---")
        users_ok = wait_for_health(USERS_SERVICE_URL, "users-service")
        trades_ok = wait_for_health(TRADES_SERVICE_URL, "trades-service")

        if not (users_ok and trades_ok):
            print("\nFAILED: Not all services became healthy")
            # Print stderr for debugging
            for name, proc, _ in processes:
                stderr = proc.stderr.read().decode() if proc.stderr else ""
                if stderr:
                    print(f"\n  {name} stderr:\n{stderr[:2000]}")
            sys.exit(1)

        # Run tests
        passed = 0
        failed = 0

        for test_fn in [
            test_cross_service_trade_with_account_validation,
            test_cross_service_trade_with_invalid_account,
            test_people_service,
            test_reference_data,
        ]:
            try:
                test_fn()
                passed += 1
            except AssertionError as e:
                print(f"  FAILED: {e}")
                failed += 1
            except Exception as e:
                print(f"  ERROR: {e}")
                failed += 1

        # Summary
        print(f"\n=== Results: {passed} passed, {failed} failed ===")
        if failed > 0:
            sys.exit(1)

    finally:
        teardown()

    print("\nAll integration tests passed!")


if __name__ == "__main__":
    main()
