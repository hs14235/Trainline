from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from core.models import Ticket
from core.services import SeatAssignmentError, assign_ticket_seat
from django.db import close_old_connections, connection
from rest_framework.test import APIClient

from .factories import PassengerFactory, TicketFactory, TrainTripFactory


@pytest.mark.postgres
@pytest.mark.django_db(transaction=True)
def test_concurrent_seat_assignment_allows_only_one_winner():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row-lock semantics are required")

    trip = TrainTripFactory()
    first = TicketFactory(passenger=PassengerFactory(), train_trip=trip)
    second = TicketFactory(passenger=PassengerFactory(), train_trip=trip)
    barrier = Barrier(2)

    def reserve(ticket_id):
        close_old_connections()
        ticket = Ticket.objects.get(pk=ticket_id)
        barrier.wait(timeout=5)
        try:
            assign_ticket_seat(ticket=ticket, seat_number="1A")
            return "reserved"
        except SeatAssignmentError as exc:
            return exc.code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(reserve, [first.pk, second.pk]))

    assert sorted(results) == ["conflict", "reserved"]
    assert Ticket.objects.filter(train_trip=trip, seat_num="1A").count() == 1


@pytest.mark.postgres
@pytest.mark.django_db(transaction=True)
def test_payment_locks_ticket_without_nullable_outer_join():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL select_for_update behavior is required")

    passenger = PassengerFactory(membership_level=None)
    ticket = TicketFactory(passenger=passenger, paid=False)
    client = APIClient()
    client.force_authenticate(user=passenger.user)

    response = client.post(
        f"/api/tickets/{ticket.pk}/pay/",
        {"payment_method": "cash"},
        format="json",
    )

    assert response.status_code == 200
    ticket.refresh_from_db()
    assert ticket.paid is True
    assert ticket.payment_method == "cash"
