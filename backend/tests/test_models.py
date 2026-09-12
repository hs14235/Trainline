import pytest
from core.models import Ticket, User
from django.db import IntegrityError

from .factories import PassengerFactory, TicketFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_user_manager_hashes_password_and_normalizes_email():
    user = User.objects.create_user(
        username="traveler",
        email="TRAVELER@EXAMPLE.TEST",
        password="DemoPass-12345",
    )

    assert user.email == "TRAVELER@example.test"
    assert user.check_password("DemoPass-12345")


def test_superuser_manager_enforces_privileged_flags():
    with pytest.raises(ValueError, match="is_staff"):
        User.objects.create_superuser(
            username="admin",
            email="admin@example.test",
            password="DemoPass-12345",
            is_staff=False,
        )


def test_passenger_is_one_to_one_with_user(user):
    PassengerFactory(user=user)

    with pytest.raises(IntegrityError):
        PassengerFactory(user=user)


def test_paid_full_service_tickets_recalculate_membership(passenger):
    TicketFactory.create_batch(
        2,
        passenger=passenger,
        paid=True,
        priority_boarding=True,
        meal=True,
        accommodation=True,
        taxi=True,
    )

    passenger.refresh_from_db()
    assert passenger.membership_points == 2
    assert passenger.membership_level.level_name == "Silver"


def test_ticket_deletion_recalculates_membership(passenger):
    tickets = TicketFactory.create_batch(
        2,
        passenger=passenger,
        paid=True,
        priority_boarding=True,
        meal=True,
        accommodation=True,
        taxi=True,
    )

    tickets[0].delete()

    passenger.refresh_from_db()
    assert passenger.membership_points == 1
    assert passenger.membership_level.level_name == "Bronze"


def test_trip_cannot_have_duplicate_nonempty_seat_assignments(trip):
    TicketFactory(train_trip=trip, seat_num="1A")

    with pytest.raises(IntegrityError):
        TicketFactory(train_trip=trip, seat_num="1A")


def test_multiple_unassigned_tickets_are_allowed(trip):
    TicketFactory.create_batch(2, train_trip=trip, seat_num=None)

    assert Ticket.objects.filter(train_trip=trip, seat_num__isnull=True).count() == 2


def test_factory_passwords_are_not_stored_in_plaintext():
    user = UserFactory()
    assert user.password != "DemoPass-12345"
    assert user.check_password("DemoPass-12345")
