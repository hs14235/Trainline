import pytest
from core.models import Ticket, User
from rest_framework.authtoken.models import Token

from .factories import SeatFactory, TrainTripFactory

pytestmark = pytest.mark.django_db


def register_and_login(client, username):
    password = f"Synthetic-{username}-Password-3817"
    registration = client.post(
        "/api/dj-rest-auth/registration/",
        {
            "username": username,
            "email": f"{username}@example.test",
            "password1": password,
            "password2": password,
        },
        format="json",
    )
    assert registration.status_code == 201, registration.data

    client.credentials()
    login = client.post(
        "/api/dj-rest-auth/login/",
        {"username": username, "password": password},
        format="json",
    )
    assert login.status_code == 200, login.data
    client.credentials(HTTP_AUTHORIZATION=f"Token {login.data['key']}")
    return password


def test_complete_booking_journey_persists_and_enforces_ownership(api_client):
    trip = TrainTripFactory(
        trip_id="JOURNEY001",
        origin_station="London St Pancras",
        destination_station="Paris Gare du Nord",
    )
    SeatFactory(train_trip=trip, seat_number="1A")
    owner_password = register_and_login(api_client, "journey_owner")

    search = api_client.get("/api/train-trips/", {"origin": "London", "destination": "Paris"})
    assert search.status_code == 200
    assert [result["trip_id"] for result in search.data] == [trip.pk]

    booking = api_client.post(
        f"/api/train-trips/{trip.pk}/book/",
        {"meal": True, "booking_key": "journey-owner-stable-key"},
        format="json",
    )
    assert booking.status_code == 201, booking.data
    ticket_id = booking.data["ticket_id"]

    payment = api_client.post(
        f"/api/tickets/{ticket_id}/pay/", {"payment_method": "cash"}, format="json"
    )
    assert payment.status_code == 200
    assert payment.data["payment_mode"] == "demo"

    seat = api_client.post(
        f"/api/seats/{trip.pk}/",
        {"ticket_id": ticket_id, "seat_num": "1A"},
        format="json",
    )
    assert seat.status_code == 200
    assert seat.data["seat_num"] == "1A"

    owner_tickets = api_client.get("/api/tickets/")
    assert owner_tickets.status_code == 200
    assert [ticket["ticket_id"] for ticket in owner_tickets.data] == [ticket_id]
    inventory = api_client.get(f"/api/seats/{trip.pk}/")
    assert inventory.status_code == 200
    assert inventory.data[0]["available"] is False

    owner_token = Token.objects.get(user__username="journey_owner")
    logout = api_client.post("/api/dj-rest-auth/logout/")
    assert logout.status_code == 200
    assert not Token.objects.filter(pk=owner_token.pk).exists()
    assert api_client.get("/api/tickets/").status_code == 401

    api_client.credentials()
    relogin = api_client.post(
        "/api/dj-rest-auth/login/",
        {"username": "journey_owner", "password": owner_password},
        format="json",
    )
    assert relogin.status_code == 200
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {relogin.data['key']}")
    persisted = api_client.get(f"/api/tickets/{ticket_id}/")
    assert persisted.status_code == 200
    assert persisted.data["paid"] is True
    assert persisted.data["seat_num"] == "1A"

    api_client.credentials()
    register_and_login(api_client, "journey_attacker")
    assert api_client.get("/api/tickets/").data == []
    assert api_client.get(f"/api/tickets/{ticket_id}/").status_code == 404
    assert (
        api_client.post(
            f"/api/tickets/{ticket_id}/pay/", {"payment_method": "cash"}, format="json"
        ).status_code
        == 404
    )
    assert (
        api_client.post(
            f"/api/seats/{trip.pk}/",
            {"ticket_id": ticket_id, "seat_num": "1A"},
            format="json",
        ).status_code
        == 404
    )
    assert api_client.delete(f"/api/tickets/{ticket_id}/").status_code == 404

    attacker_booking = api_client.post(
        f"/api/train-trips/{trip.pk}/book/",
        {"booking_key": "journey-attacker-stable-key"},
        format="json",
    )
    attacker_ticket_id = attacker_booking.data["ticket_id"]
    assert (
        api_client.post(
            f"/api/tickets/{attacker_ticket_id}/pay/",
            {"payment_method": "cash"},
            format="json",
        ).status_code
        == 200
    )
    occupied = api_client.post(
        f"/api/seats/{trip.pk}/",
        {"ticket_id": attacker_ticket_id, "seat_num": "1A"},
        format="json",
    )
    assert occupied.status_code == 409
    assert Ticket.objects.get(pk=attacker_ticket_id).seat_num is None
    assert User.objects.filter(username="journey_owner").exists()
