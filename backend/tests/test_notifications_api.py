import pytest
from core.models import Notification

from .factories import NotificationFactory, TicketFactory

pytestmark = pytest.mark.django_db


def test_notification_list_is_user_scoped(authenticated_client, user):
    own_notification = NotificationFactory(user=user)
    NotificationFactory()

    response = authenticated_client.get("/api/notifications/")

    assert response.status_code == 200
    assert [item["notification_id"] for item in response.data] == [own_notification.pk]


def test_user_can_mark_own_notification_read(authenticated_client, user):
    notification = NotificationFactory(user=user, read_status="unread")

    response = authenticated_client.post(
        f"/api/notifications/{notification.pk}/mark_read/", {}, format="json"
    )

    assert response.status_code == 200
    notification.refresh_from_db()
    assert notification.read_status == "read"


def test_user_cannot_access_or_mark_other_notification(authenticated_client):
    notification = NotificationFactory()

    assert authenticated_client.get(f"/api/notifications/{notification.pk}/").status_code == 404
    assert (
        authenticated_client.post(
            f"/api/notifications/{notification.pk}/mark_read/", {}, format="json"
        ).status_code
        == 404
    )


def test_structured_notification_is_event_snapshot_and_idempotent(user):
    ticket = TicketFactory(passenger__user=user)
    defaults = {
        "event_type": "seat_confirmed",
        "ticket": ticket,
        "train_trip": ticket.train_trip,
        "title": "Seat confirmed",
        "message": "Seat 1A is confirmed.",
        "booking_reference": f"TL-{ticket.pk:06d}",
        "route_snapshot": "London St Pancras → Paris Gare du Nord",
        "seat_snapshot": "1A",
        "points_delta": 1,
    }
    Notification.objects.get_or_create(user=user, event_key="seat:test", defaults=defaults)
    Notification.objects.get_or_create(user=user, event_key="seat:test", defaults=defaults)
    note = Notification.objects.get(user=user, event_key="seat:test")
    ticket.delete()
    note.refresh_from_db()
    assert Notification.objects.filter(user=user, event_key="seat:test").count() == 1
    assert note.ticket is None
    assert note.route_snapshot == "London St Pancras → Paris Gare du Nord"
