import pytest
from django.db import connection


def test_liveness_does_not_require_authentication(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_readiness_executes_database_query(client):
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_readiness_hides_database_error_details(client, monkeypatch):
    def fail_cursor(*args, **kwargs):
        raise RuntimeError("sensitive database details")

    monkeypatch.setattr(connection, "cursor", fail_cursor)
    response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert b"sensitive" not in response.content
