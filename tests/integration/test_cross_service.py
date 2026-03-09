"""Integration test — starts all extracted services, verifies /health endpoints,
and runs a cross-service operation (create account → submit trade → check position).

Usage:
    TENANT_ID=test_tenant python tests/integration/test_cross_service.py
"""

import os
import signal
import subprocess
import sys
import time

import httpx

TENANT_ID = os.environ.get("TENANT_ID")
if not TENANT_ID:
    print("FATAL: TENANT_ID environment variable is required.")
    sys.exit(1)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SERVICES = [
    {"name": "account-service",        "port": 8001, "dir": "services/account-service"},
    {"name": "trading-service",        "port": 8002, "dir": "services/trading-service"},
    {"name": "position-service",       "port": 8003, "dir": "services/position-service"},
    {"name": "reference-data-service", "port": 8004, "dir": "services/reference-data-service"},
    {"name": "people-service",         "port": 8005, "dir": "services/people-service"},
]

processes = []


def start_services():
    """Start all services in the background."""
    env = os.environ.copy()
    env["TENANT_ID"] = TENANT_ID

    for svc in SERVICES:
        svc_dir = os.path.join(REPO_ROOT, svc["dir"])
        env_copy = env.copy()
        env_copy["SERVICE_PORT"] = str(svc["port"])
        proc = subprocess.Popen(
            [sys.executable, "run.py"],
            cwd=svc_dir,
            env=env_copy,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        processes.append(proc)
        print(f"  Started {svc['name']} (PID {proc.pid}) on port {svc['port']}")


def wait_for_health(timeout=30):
    """Wait for all services to be healthy."""
    deadline = time.time() + timeout
    for svc in SERVICES:
        url = f"http://localhost:{svc['port']}/health"
        while time.time() < deadline:
            try:
                resp = httpx.get(url, timeout=2.0)
                if resp.status_code == 200:
                    data = resp.json()
                    assert data["status"] == "UP", f"{svc['name']} health status != UP"
                    assert data["service"] == svc["name"], f"{svc['name']} service name mismatch"
                    assert data["tenant"] == TENANT_ID, f"{svc['name']} tenant mismatch"
                    print(f"  {svc['name']} healthy: {data}")
                    break
            except (httpx.RequestError, AssertionError):
                time.sleep(0.5)
        else:
            print(f"  TIMEOUT waiting for {svc['name']} at {url}")
            return False
    return True


def test_cross_service_operation():
    """Test a cross-service operation: create account → submit trade → check position."""
    print("\n--- Cross-service operation test ---")

    # 1. Create an account via Account Service
    print("  Creating account...")
    resp = httpx.post(
        "http://localhost:8001/account/",
        json={"id": 9001, "displayName": "Integration Test Account"},
        timeout=5.0,
    )
    assert resp.status_code == 200, f"Account creation failed: {resp.status_code} {resp.text}"
    account = resp.json()
    print(f"  Account created: {account}")

    # 2. Verify account exists
    resp = httpx.get("http://localhost:8001/account/9001", timeout=5.0)
    assert resp.status_code == 200, f"Account fetch failed: {resp.status_code}"
    print("  Account verified via GET")

    # 3. Submit a trade via Trading Service
    print("  Submitting trade...")
    resp = httpx.post(
        "http://localhost:8002/trade/",
        json={"accountId": 9001, "security": "AAPL", "side": "Buy", "quantity": 100},
        timeout=10.0,
    )
    assert resp.status_code == 200, f"Trade submission failed: {resp.status_code} {resp.text}"
    trade_result = resp.json()
    print(f"  Trade result: success={trade_result['success']} state={trade_result['trade']['state']}")
    assert trade_result["success"] is True, "Trade was not successful"

    # 4. Check positions via Position Service
    print("  Checking positions...")
    resp = httpx.get("http://localhost:8003/positions/9001", timeout=5.0)
    assert resp.status_code == 200, f"Position fetch failed: {resp.status_code}"
    positions = resp.json()
    print(f"  Positions for account 9001: {positions}")
    assert len(positions) >= 1, "Expected at least one position after trade"
    assert positions[0]["security"] == "AAPL"
    assert positions[0]["quantity"] == 100

    # 5. Verify reference data is accessible
    print("  Checking reference data...")
    resp = httpx.get("http://localhost:8004/stocks/AAPL", timeout=5.0)
    assert resp.status_code == 200, f"Reference data fetch failed: {resp.status_code}"
    print(f"  Stock data: {resp.json()}")

    # 6. Check people service
    print("  Checking people service...")
    resp = httpx.get(
        "http://localhost:8005/people/ValidatePerson",
        params={"LogonId": "nonexistent"},
        timeout=5.0,
    )
    assert resp.status_code == 200, f"People service failed: {resp.status_code}"
    print(f"  People validation: {resp.json()}")

    print("\n  All cross-service operations passed!")


def stop_services():
    """Stop all background services."""
    for proc in processes:
        try:
            os.kill(proc.pid, signal.SIGTERM)
            proc.wait(timeout=5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            proc.kill()
    print("  All services stopped.")


def cleanup_db_files():
    """Remove tenant-specific database files generated during tests."""
    for svc in SERVICES:
        svc_dir = os.path.join(REPO_ROOT, svc["dir"])
        for f in os.listdir(svc_dir):
            if f.startswith("app_") and f.endswith(".db"):
                os.remove(os.path.join(svc_dir, f))
                print(f"  Removed {svc['dir']}/{f}")


def main():
    print(f"=== Integration Test (TENANT_ID={TENANT_ID}) ===\n")

    print("Starting services...")
    start_services()

    print("\nWaiting for health checks...")
    if not wait_for_health():
        print("\nFAILED: Not all services became healthy.")
        stop_services()
        cleanup_db_files()
        sys.exit(1)

    try:
        test_cross_service_operation()
        print("\n=== INTEGRATION TEST PASSED ===")
    except AssertionError as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
    finally:
        print("\nStopping services...")
        stop_services()
        print("\nCleaning up DB files...")
        cleanup_db_files()


if __name__ == "__main__":
    main()
