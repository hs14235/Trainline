import pytest

from .factories import SeatFactory, TicketFactory, TrainTripFactory

pytestmark = pytest.mark.django_db


def test_available_seats_come_from_configured_inventory(authenticated_client, passenger, trip):
    SeatFactory(train_trip=trip, car_number="1", seat_number="1A")
    SeatFactory(train_trip=trip, car_number="1", seat_number="1B")
    TicketFactory(passenger=passenger, train_trip=trip, seat_num="1A")

    response = authenticated_client.get(f"/api/seats/{trip.pk}/")

    assert response.status_code == 200
    assert response.data == [
        {"seat_number": "1A", "car_number": "1", "travel_class": "standard", "available": False},
        {"seat_number": "1B", "car_number": "1", "travel_class": "standard", "available": True},
    ]


def test_unknown_trip_seat_list_returns_404(authenticated_client):
    assert authenticated_client.get("/api/seats/missing/").status_code == 404


def test_seat_assignment_normalizes_input(authenticated_client, passenger, trip):
    SeatFactory(train_trip=trip, car_number="1", seat_number="1A", travel_class="first")
    ticket = TicketFactory(passenger=passenger, train_trip=trip, paid=True)

    response = authenticated_client.post(
        f"/api/seats/{trip.pk}/",
        {"ticket_id": ticket.pk, "seat_num": " 1a "},
        format="json",
    )

    assert response.status_code == 200
    ticket.refresh_from_db()
    assert ticket.seat_num == "1A"
    assert response.data["first_class_bonus"] is True
    passenger.refresh_from_db()
    assert passenger.membership_points == 1


@pytest.mark.parametrize(
    ("payload", "expected_status"),
    [
        ({"seat_num": "1A"}, 400),
        ({"ticket_id": "not-an-integer", "seat_num": "1A"}, 400),
        ({"ticket_id": 1, "seat_num": "Priority BoardingA"}, 404),
    ],
)
def test_seat_assignment_rejects_malformed_payloads(authenticated_client, payload, expected_status):
    trip = TrainTripFactory()
    response = authenticated_client.post(f"/api/seats/{trip.pk}/", payload, format="json")
    assert response.status_code == expected_status


def test_seat_assignment_rejects_unknown_configured_seat(authenticated_client, passenger, trip):
    SeatFactory(train_trip=trip, seat_number="1A")
    ticket = TicketFactory(passenger=passenger, train_trip=trip, paid=True)

    response = authenticated_client.post(
        f"/api/seats/{trip.pk}/",
        {"ticket_id": ticket.pk, "seat_num": "2A"},
        format="json",
    )

    assert response.status_code == 400
    assert response.data["seat_num"] == ["That seat is not part of this coach."]


def test_seat_assignment_rejects_ticket_from_other_trip(authenticated_client, passenger, trip):
    ticket = TicketFactory(passenger=passenger, train_trip=TrainTripFactory(), paid=True)

    response = authenticated_client.post(
        f"/api/seats/{trip.pk}/",
        {"ticket_id": ticket.pk, "seat_num": "1A"},
        format="json",
    )

    assert response.status_code == 400


def test_seat_assignment_hides_other_users_ticket(authenticated_client, trip):
    other_ticket = TicketFactory(train_trip=trip, paid=True)

    response = authenticated_client.post(
        f"/api/seats/{trip.pk}/",
        {"ticket_id": other_ticket.pk, "seat_num": "1A"},
        format="json",
    )

    assert response.status_code == 404


def test_duplicate_seat_returns_conflict(authenticated_client, passenger, trip):
    TicketFactory(train_trip=trip, seat_num="1A")
    ticket = TicketFactory(passenger=passenger, train_trip=trip, paid=True)

    response = authenticated_client.post(
        f"/api/seats/{trip.pk}/",
        {"ticket_id": ticket.pk, "seat_num": "1A"},
        format="json",
    )

    assert response.status_code == 409
    ticket.refresh_from_db()
    assert ticket.seat_num is None


def test_ticket_patch_uses_same_conflict_protection(authenticated_client, passenger, trip):
    TicketFactory(train_trip=trip, seat_num="1A")
    ticket = TicketFactory(passenger=passenger, train_trip=trip, paid=True)

    response = authenticated_client.patch(
        f"/api/tickets/{ticket.pk}/", {"seat_num": "1A"}, format="json"
    )

    assert response.status_code == 409
    ticket.refresh_from_db()
    assert ticket.seat_num is None


def test_unpaid_ticket_cannot_choose_seat(authenticated_client, passenger, trip):
    SeatFactory(train_trip=trip, seat_number="1A")
    ticket = TicketFactory(passenger=passenger, train_trip=trip, paid=False)
    response = authenticated_client.post(
        f"/api/seats/{trip.pk}/", {"ticket_id": ticket.pk, "seat_num": "1A"}, format="json"
    )
    assert response.status_code == 400
    assert "Complete demo payment" in str(response.data)
