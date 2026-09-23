from decimal import Decimal

import pytest

from .factories import PassengerFactory, TicketFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_ticket_list_is_scoped_to_authenticated_user(authenticated_client, passenger):
    own_ticket = TicketFactory(passenger=passenger)
    TicketFactory()

    response = authenticated_client.get("/api/tickets/")

    assert response.status_code == 200
    assert [ticket["ticket_id"] for ticket in response.data] == [own_ticket.pk]


def test_cross_user_ticket_retrieve_update_and_delete_return_404(authenticated_client):
    other_ticket = TicketFactory()

    assert authenticated_client.get(f"/api/tickets/{other_ticket.pk}/").status_code == 404
    assert (
        authenticated_client.patch(
            f"/api/tickets/{other_ticket.pk}/", {"meal": True}, format="json"
        ).status_code
        == 404
    )
    assert authenticated_client.delete(f"/api/tickets/{other_ticket.pk}/").status_code == 404


def test_create_ignores_attacker_supplied_passenger(authenticated_client, passenger):
    other_passenger = PassengerFactory(user=UserFactory())

    response = authenticated_client.post(
        "/api/tickets/",
        {"passenger": other_passenger.pk, "meal": True},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["passenger"] == passenger.pk


def test_amenity_update_recalculates_server_amount(authenticated_client, passenger):
    ticket = TicketFactory(passenger=passenger, amount=Decimal("100.00"))

    response = authenticated_client.patch(
        f"/api/tickets/{ticket.pk}/",
        {"meal": True, "taxi": True, "amount": "0.01"},
        format="json",
    )

    assert response.status_code == 200
    ticket.refresh_from_db()
    assert ticket.amount == Decimal("170.00")


def test_paid_ticket_amenities_cannot_change(authenticated_client, passenger):
    ticket = TicketFactory(passenger=passenger, paid=True)

    response = authenticated_client.patch(
        f"/api/tickets/{ticket.pk}/", {"meal": True}, format="json"
    )

    assert response.status_code == 400
    assert "Paid tickets" in str(response.data)


@pytest.mark.parametrize("payment_method", ["cash", "check", "credit_card"])
def test_payment_accepts_supported_methods(authenticated_client, passenger, payment_method):
    ticket = TicketFactory(passenger=passenger)

    response = authenticated_client.post(
        f"/api/tickets/{ticket.pk}/pay/",
        {"payment_method": payment_method},
        format="json",
    )

    assert response.status_code == 200
    ticket.refresh_from_db()
    assert ticket.paid is True
    assert ticket.payment_method == payment_method


def test_payment_awards_priority_point_once_and_creates_durable_events(
    authenticated_client, passenger
):
    ticket = TicketFactory(passenger=passenger, priority_boarding=True)
    endpoint = f"/api/tickets/{ticket.pk}/pay/"
    response = authenticated_client.post(endpoint, {"payment_method": "cash"}, format="json")
    assert response.status_code == 200
    passenger.refresh_from_db()
    assert passenger.membership_points == 1
    assert passenger.user.notification_set.filter(event_key=f"payment:{ticket.pk}").count() == 1
    assert (
        passenger.user.notification_set.filter(event_key=f"points:priority:{ticket.pk}").count()
        == 1
    )


def test_payment_rejects_missing_and_unknown_methods(authenticated_client, passenger):
    ticket = TicketFactory(passenger=passenger)

    missing = authenticated_client.post(f"/api/tickets/{ticket.pk}/pay/", {}, format="json")
    unknown = authenticated_client.post(
        f"/api/tickets/{ticket.pk}/pay/",
        {"payment_method": "crypto"},
        format="json",
    )

    assert missing.status_code == 400
    assert unknown.status_code == 400


def test_duplicate_payment_is_conflict(authenticated_client, passenger):
    ticket = TicketFactory(passenger=passenger)
    endpoint = f"/api/tickets/{ticket.pk}/pay/"

    assert (
        authenticated_client.post(endpoint, {"payment_method": "cash"}, format="json").status_code
        == 200
    )
    second = authenticated_client.post(endpoint, {"payment_method": "cash"}, format="json")

    assert second.status_code == 409


def test_ticket_delete_cancels_only_owned_ticket(authenticated_client, passenger):
    ticket = TicketFactory(passenger=passenger)
    response = authenticated_client.delete(f"/api/tickets/{ticket.pk}/")
    assert response.status_code == 204
