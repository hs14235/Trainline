from decimal import Decimal

import pytest
from core.models import Ticket
from django.utils import timezone

from .factories import TrainTripFactory

pytestmark = pytest.mark.django_db


def test_trip_list_filters_origin_destination_and_status(authenticated_client):
    matching = TrainTripFactory(
        origin_station="London St Pancras",
        destination_station="Paris Gare du Nord",
        status="Scheduled",
    )
    TrainTripFactory(origin_station="Berlin Hbf", destination_station="Paris Gare du Nord")
    TrainTripFactory(origin_station="London Victoria", destination_station="Brighton")

    response = authenticated_client.get(
        "/api/train-trips/",
        {"origin": "london", "destination": "paris", "status": "scheduled"},
    )

    assert response.status_code == 200
    assert [trip["trip_id"] for trip in response.data] == [matching.trip_id]


def test_trip_list_uses_allowlisted_ordering(authenticated_client):
    later = TrainTripFactory(departure_time=timezone.now().replace(microsecond=0))
    earlier = TrainTripFactory(departure_time=later.departure_time.replace(year=2025))

    response = authenticated_client.get("/api/train-trips/", {"ordering": "departure_time"})

    assert [trip["trip_id"] for trip in response.data] == [earlier.trip_id, later.trip_id]


def test_unknown_ordering_falls_back_without_exposing_arbitrary_fields(authenticated_client, trip):
    response = authenticated_client.get("/api/train-trips/", {"ordering": "password"})
    assert response.status_code == 200
    assert response.data[0]["trip_id"] == trip.trip_id


def test_booking_calculates_amount_server_side(authenticated_client, user, trip):
    response = authenticated_client.post(
        f"/api/train-trips/{trip.pk}/book/",
        {
            "priority_boarding": True,
            "meal": "yes",
            "accommodation": 1,
            "taxi": "on",
            "amount": "0.01",
        },
        format="json",
    )

    assert response.status_code == 201
    ticket = Ticket.objects.get(pk=response.data["ticket_id"])
    assert ticket.passenger.user == user
    assert ticket.amount == Decimal("280.00")
    assert response.data["amount"] == "280.00"
    assert response.data["quote"]["taxes_and_fees"] == "0.00"
    assert response.data["quote"]["total"] == "280.00"


def test_quote_and_booking_are_server_authoritative_and_idempotent(authenticated_client, trip):
    quote = authenticated_client.get(
        f"/api/train-trips/{trip.pk}/quote/", {"priority_boarding": "true", "meal": "true"}
    )
    assert quote.status_code == 200
    assert quote.data["total"] == "180.00"
    assert quote.data["tax_rule"].startswith("No taxes")

    payload = {"priority_boarding": True, "booking_key": "stable-client-key"}
    first = authenticated_client.post(f"/api/train-trips/{trip.pk}/book/", payload, format="json")
    second = authenticated_client.post(f"/api/train-trips/{trip.pk}/book/", payload, format="json")
    assert first.status_code == 201
    assert second.status_code == 200
    assert second.data["ticket_id"] == first.data["ticket_id"]
    assert Ticket.objects.filter(booking_key="stable-client-key").count() == 1


def test_booking_unknown_trip_returns_404(authenticated_client):
    response = authenticated_client.post("/api/train-trips/missing/book/", {}, format="json")
    assert response.status_code == 404
