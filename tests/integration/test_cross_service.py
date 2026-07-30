#!/usr/bin/env python3
"""
Cross-service integration test for the extracted TraderX services.

Starts all five services with a single TENANT_ID, waits for their /health endpoints,
exercises an end-to-end trade (which forces account-service, reference-data-service,
position-service and trading-service to talk to each other over HTTP), then tears the
services down.

Run:
    TENANT_ID=test_tenant python tests/integration/test_cross_service.py
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICES_DIR = REPO_ROOT / "services"

TENANT_ID = os.environ.get("TENANT_ID", "test_tenant")

SERVICES = [
    ("account-service", 8001),
    ("trading-service", 8002),
    ("position-service", 8003),
    ("reference-data-service", 8004),
    ("people-service", 8005),
]

STARTUP_TIMEOUT_S = 60
HTTP_TIMEOUT_S = 10


class TestFailure(AssertionError):
    pass


def check(condition, message):
    if not condition:
        raise TestFailure(message)


def service_env(port):
    env = dict(os.environ)
    env.update(
        {
            "TENANT_ID": TENANT_ID,
            "PORT": str(port),
            "ACCOUNT_SERVICE_URL": "http://localhost:8001",
            "TRADING_SERVICE_URL": "http://localhost:8002",
            "POSITION_SERVICE_URL": "http://localhost:8003",
            "REFERENCE_DATA_SERVICE_URL": "http://localhost:8004",
            "PEOPLE_SERVICE_URL": "http://localhost:8005",
        }
    )
    env.pop("DATABASE_URL", None)
    return env


def start_services():
    processes = {}
    for name, port in SERVICES:
        service_dir = SERVICES_DIR / name
        check(service_dir.is_dir(), f"missing service directory: {service_dir}")
        log = open(f"/tmp/{name}-integration.log", "w")
        processes[name] = (
            subprocess.Popen(
                [sys.executable, "run.py"],
                cwd=service_dir,
                env=service_env(port),
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            ),
            log,
        )
        print(f"started {name} on port {port} (pid {processes[name][0].pid})")
    return processes


def stop_services(processes):
    for name, (process, log) in processes.items():
        if process.poll() is None:
            # SIGTERM must be handled gracefully by every service.
            process.terminate()
            try:
                process.wait(timeout=15)
                print(f"{name} shut down gracefully on SIGTERM")
            except subprocess.TimeoutExpired:
                print(f"{name} did not exit on SIGTERM, killing")
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        log.close()


def wait_for_health():
    deadline = time.time() + STARTUP_TIMEOUT_S
    for name, port in SERVICES:
        url = f"http://localhost:{port}/health"
        while True:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    break
            except requests.RequestException:
                pass
            check(
                time.time() < deadline,
                f"{name} did not become healthy within {STARTUP_TIMEOUT_S}s "
                f"(see /tmp/{name}-integration.log)",
            )
            time.sleep(0.5)


def test_health_contract():
    for name, port in SERVICES:
        body = requests.get(f"http://localhost:{port}/health", timeout=HTTP_TIMEOUT_S).json()
        check(
            body == {"status": "UP", "service": name, "tenant": TENANT_ID},
            f"{name} /health returned {body}",
        )
    print("PASS: every service reports UP for tenant", TENANT_ID)


def test_openapi_specs():
    for name, port in SERVICES:
        spec = requests.get(f"http://localhost:{port}/openapi.json", timeout=HTTP_TIMEOUT_S)
        check(spec.status_code == 200, f"{name} has no OpenAPI spec ({spec.status_code})")
        check("paths" in spec.json(), f"{name} OpenAPI spec has no paths")
    print("PASS: every service serves an OpenAPI spec")


def test_mismatched_tenant_is_rejected():
    for name, port in SERVICES:
        response = requests.get(
            f"http://localhost:{port}/health",
            headers={"X-Tenant-ID": "some_other_tenant"},
            timeout=HTTP_TIMEOUT_S,
        )
        check(response.status_code == 403, f"{name} accepted a foreign tenant header")
    print("PASS: every service rejects a mismatched X-Tenant-ID with 403")


def test_end_to_end_trade():
    """account-service -> people-service, trading-service -> account/reference-data/position."""
    account = requests.post(
        "http://localhost:8001/account/",
        json={"displayName": "Integration Test Account"},
        timeout=HTTP_TIMEOUT_S,
    )
    check(account.status_code == 200, f"account creation failed: {account.status_code} {account.text}")
    account_id = account.json()["id"]
    print(f"created account {account_id}")

    search = requests.get(
        "http://localhost:8005/people/GetMatchingPeople",
        params={"SearchText": "smith"},
        timeout=HTTP_TIMEOUT_S,
    )
    check(search.status_code == 200, f"people search failed: {search.status_code} {search.text}")
    payload = search.json()
    people = payload.get("People", payload) if isinstance(payload, dict) else payload
    check(len(people) > 0, "people-service returned no people to attach to the account")
    logon_id = people[0].get("logonId") or people[0].get("LogonId")
    check(logon_id, f"people-service response has no logon id: {people[0]}")

    account_user = requests.post(
        "http://localhost:8001/accountuser/",
        json={"accountId": account_id, "username": logon_id},
        timeout=HTTP_TIMEOUT_S,
    )
    check(
        account_user.status_code == 200,
        f"account user creation failed (account-service -> people-service): "
        f"{account_user.status_code} {account_user.text}",
    )
    print(f"attached user {logon_id} to account {account_id} via people-service validation")

    unknown = requests.post(
        "http://localhost:8002/trade/",
        json={"accountId": account_id, "security": "NOTATICKER", "side": "Buy", "quantity": 1},
        timeout=HTTP_TIMEOUT_S,
    )
    check(
        unknown.status_code >= 400 or unknown.json().get("success") is False,
        "trading-service accepted a trade for an unknown security "
        "(reference-data-service validation is not wired up)",
    )
    print("rejected unknown security via reference-data-service")

    trade = requests.post(
        "http://localhost:8002/trade/",
        json={"accountId": account_id, "security": "AAPL", "side": "Buy", "quantity": 100},
        timeout=HTTP_TIMEOUT_S,
    )
    check(trade.status_code == 200, f"trade submission failed: {trade.status_code} {trade.text}")
    body = trade.json()
    check(body.get("success") is True, f"trade was not successful: {body}")
    print(f"submitted trade: {body['trade']}")

    positions = requests.get(
        f"http://localhost:8003/positions/{account_id}", timeout=HTTP_TIMEOUT_S
    ).json()
    aapl = [p for p in positions if p.get("security") == "AAPL"]
    check(aapl, f"position-service has no AAPL position for account {account_id}: {positions}")
    check(
        aapl[0]["quantity"] == 100,
        f"expected quantity 100 after the trade, got {aapl[0]['quantity']}",
    )
    print("PASS: trading-service updated the position in position-service over HTTP")

    account_detail = requests.get(
        f"http://localhost:8001/account/{account_id}", timeout=HTTP_TIMEOUT_S
    ).json()
    embedded = account_detail.get("positions", [])
    check(
        any(p.get("security") == "AAPL" for p in embedded),
        f"account-service did not compose positions from position-service: {account_detail}",
    )
    print("PASS: account-service composed positions from position-service over HTTP")


def main():
    print(f"=== TraderX cross-service integration test (tenant: {TENANT_ID}) ===")
    processes = start_services()
    try:
        wait_for_health()
        test_health_contract()
        test_openapi_specs()
        test_mismatched_tenant_is_rejected()
        test_end_to_end_trade()
    except TestFailure as failure:
        print(f"\nFAILED: {failure}")
        return 1
    finally:
        stop_services(processes)
    print("\nAll cross-service integration checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
