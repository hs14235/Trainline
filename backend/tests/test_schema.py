import pytest


@pytest.mark.django_db
def test_openapi_schema_exposes_core_workflows(api_client):
    response = api_client.get("/api/schema/")

    assert response.status_code == 200
    schema = response.content.decode()
    assert "/api/train-trips/" in schema
    assert "/api/tickets/{ticket_id}/pay/" in schema
    assert "/api/seats/{flight_id}/" in schema
    assert "/api/notifications/{notification_id}/mark_read/" in schema
