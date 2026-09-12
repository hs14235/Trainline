from decimal import Decimal

import pytest
from core.serializers import TicketSerializer

from .factories import PassengerFactory, TicketFactory

pytestmark = pytest.mark.django_db


def test_ticket_server_controlled_fields_ignore_input(passenger):
    other_passenger = PassengerFactory()
    ticket = TicketFactory(passenger=passenger, amount=Decimal("100.00"), paid=False)
    serializer = TicketSerializer(
        ticket,
        data={
            "passenger": other_passenger.pk,
            "amount": "0.01",
            "paid": True,
            "payment_method": "cash",
            "meal": True,
        },
        partial=True,
    )

    assert serializer.is_valid(), serializer.errors
    updated = serializer.save()
    assert updated.passenger == passenger
    assert updated.amount == Decimal("100.00")
    assert updated.paid is False
    assert updated.payment_method is None
    assert updated.meal is True


def test_paid_ticket_rejects_amenity_mutation():
    ticket = TicketFactory(paid=True)
    serializer = TicketSerializer(ticket, data={"meal": True}, partial=True)

    assert serializer.is_valid() is False
    assert "Paid tickets" in str(serializer.errors)
