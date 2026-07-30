"""Tests for single-tenant runtime enforcement."""
import os
import subprocess
import sys

from tests.conftest import TEST_TENANT_ID


def test_health_reports_startup_tenant(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {
        "status": "UP",
        "service": "TraderX Monolith API",
        "tenant": TEST_TENANT_ID,
    }


def test_request_without_tenant_header_uses_startup_tenant(client):
    resp = client.post("/account/", json={"displayName": "Implicit Tenant"})
    assert resp.status_code == 200
    assert resp.json()["tenant_id"] == TEST_TENANT_ID


def test_request_with_matching_tenant_header_is_allowed(client):
    resp = client.get("/account/", headers={"X-Tenant-ID": TEST_TENANT_ID})
    assert resp.status_code == 200


def test_request_with_mismatched_tenant_header_is_rejected(client):
    resp = client.get("/account/", headers={"X-Tenant-ID": "other_tenant"})
    assert resp.status_code == 403
    assert TEST_TENANT_ID in resp.json()["detail"]


def test_app_fails_fast_without_tenant_id():
    env = {k: v for k, v in os.environ.items() if k != "TENANT_ID"}
    result = subprocess.run(
        [sys.executable, "-c", "import app.config"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "TENANT_ID environment variable is required" in result.stderr
