import pytest
from rest_framework.test import APIClient

from .factories import PassengerFactory, TrainTripFactory, UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def passenger(user):
    return PassengerFactory(user=user)


@pytest.fixture
def trip(db):
    return TrainTripFactory()


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client
