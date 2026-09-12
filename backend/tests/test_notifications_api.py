import pytest

from .factories import NotificationFactory

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
