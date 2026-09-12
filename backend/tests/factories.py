from datetime import timedelta
from decimal import Decimal

import factory
from core.models import MembershipLevel, Notification, Passenger, Seat, Ticket, TrainTrip, User
from django.utils import timezone
from factory.django import DjangoModelFactory


class MembershipLevelFactory(DjangoModelFactory):
    class Meta:
        model = MembershipLevel
        django_get_or_create = ("level_name",)

    level_name = "Bronze"
    min_points_required = 0
    perks_description = "Welcome aboard"


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda number: f"user{number}")
    email = factory.LazyAttribute(lambda user: f"{user.username}@example.test")
    first_name = "Demo"
    last_name = "Traveler"
    password = "DemoPass-12345"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)


class PassengerFactory(DjangoModelFactory):
    class Meta:
        model = Passenger

    user = factory.SubFactory(UserFactory)
    full_name = factory.LazyAttribute(lambda passenger: passenger.user.get_full_name())
    passport_number = factory.Sequence(lambda number: f"DEMO-PASSPORT-{number:05d}")


class TrainTripFactory(DjangoModelFactory):
    class Meta:
        model = TrainTrip

    trip_id = factory.Sequence(lambda number: f"T{number:05d}")
    service_number = factory.Sequence(lambda number: 7000 + number)
    origin_station = "London St Pancras"
    destination_station = "Paris Gare du Nord"
    departure_time = factory.LazyFunction(lambda: timezone.now() + timedelta(days=1))
    arrival_time = factory.LazyAttribute(
        lambda trip: trip.departure_time + timedelta(hours=2, minutes=20)
    )
    status = "Scheduled"
    consist_type = "Electric multiple unit"
    platform = "5"


class SeatFactory(DjangoModelFactory):
    class Meta:
        model = Seat

    train_trip = factory.SubFactory(TrainTripFactory)
    car_number = "1"
    seat_number = factory.Sequence(lambda number: f"{number + 1}A")
    travel_class = "standard"


class TicketFactory(DjangoModelFactory):
    class Meta:
        model = Ticket

    passenger = factory.SubFactory(PassengerFactory)
    train_trip = factory.SubFactory(TrainTripFactory)
    amount = Decimal("100.00")


class NotificationFactory(DjangoModelFactory):
    class Meta:
        model = Notification

    user = factory.SubFactory(UserFactory)
    train_trip = factory.SubFactory(TrainTripFactory)
    message = "Your train is ready for boarding."
    sent_date = factory.LazyFunction(timezone.now)
    read_status = "unread"
