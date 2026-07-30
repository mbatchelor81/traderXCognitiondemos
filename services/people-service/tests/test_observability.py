"""Correlation ID, structured logging and no-peer-dependency tests."""

import json
import logging
import socket

from app.logging_config import JsonFormatter


def test_correlation_id_is_echoed_when_supplied(client):
    response = client.get("/health", headers={"X-Correlation-ID": "corr-123"})
    assert response.headers["X-Correlation-ID"] == "corr-123"


def test_correlation_id_is_generated_when_absent(client):
    response = client.get("/health")
    assert response.headers.get("X-Correlation-ID")


def test_json_formatter_emits_required_fields():
    record = logging.LogRecord(
        name="app.test", level=logging.INFO, pathname=__file__, lineno=1,
        msg="something_happened", args=(), exc_info=None,
    )
    record.correlation_id = "corr-123"
    entry = json.loads(JsonFormatter().format(record))

    assert entry["message"] == "something_happened"
    assert entry["level"] == "INFO"
    assert entry["service"] == "people-service"
    assert entry["tenant_id"]
    assert entry["timestamp"]
    assert entry["correlation_id"] == "corr-123"


def test_request_timing_is_logged(client, caplog):
    with caplog.at_level(logging.INFO, logger="app.middleware"):
        client.get("/health")

    timing_records = [r for r in caplog.records if r.message == "request_completed"]
    assert timing_records
    record = timing_records[-1]
    assert record.method == "GET"
    assert record.path == "/health"
    assert record.status_code == 200
    assert record.duration_ms >= 0


def test_endpoints_need_no_peer_services(client, monkeypatch):
    """people-service makes no outbound HTTP calls; break sockets to prove it."""

    def _no_network(*args, **kwargs):
        raise AssertionError("people-service must not open outbound connections")

    monkeypatch.setattr(socket.socket, "connect", _no_network)
    monkeypatch.setattr(socket, "create_connection", _no_network)

    assert client.get("/health").status_code == 200
    assert client.get("/people/GetPerson", params={"LogonId": "jsmith"}).status_code == 200
    assert client.get("/people/ValidatePerson", params={"LogonId": "jsmith"}).status_code == 200
    assert client.get(
        "/people/GetMatchingPeople", params={"SearchText": "smith"}
    ).status_code == 200
