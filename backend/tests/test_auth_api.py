import pytest
from core.models import User
from rest_framework.authtoken.models import Token

pytestmark = pytest.mark.django_db


def test_anonymous_user_cannot_list_trips(api_client):
    response = api_client.get("/api/train-trips/")
    assert response.status_code == 401


def test_login_returns_token(api_client, user):
    response = api_client.post(
        "/api/dj-rest-auth/login/",
        {"username": user.username, "password": "DemoPass-12345"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["key"] == Token.objects.get(user=user).key


def test_registration_creates_user(api_client):
    response = api_client.post(
        "/api/dj-rest-auth/registration/",
        {
            "username": "newtraveler",
            "email": "newtraveler@example.test",
            "password1": "Strong-Demo-Pass-3817",
            "password2": "Strong-Demo-Pass-3817",
        },
        format="json",
    )

    assert response.status_code == 201, response.data
    assert User.objects.filter(username="newtraveler").exists()


def test_me_returns_only_authenticated_user(authenticated_client, user, passenger):
    response = authenticated_client.get("/api/me/")

    assert response.status_code == 200
    assert response.data["username"] == user.username
    assert response.data["email"] == user.email
    assert response.data["membership_points"] == 0
