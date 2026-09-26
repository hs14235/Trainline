from datetime import datetime, timezone

from core.models import (
    ChatMessage,
    Notification,
    Passenger,
    Payment,
    Seat,
    Ticket,
    TrainTrip,
    User,
)
from core.services import calculate_ticket_amount
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import models, transaction

DEMO_TRIP_IDS = ("DEMO001", "DEMO002", "DEMO003")
DEMO_PAYMENT_IDS = (9001, 9002)
DEMO_CHAT_IDS = (9001, 9002)
DEVELOPMENT_DEMO_PASSWORD = "Trainline-Demo-2026!"


class Command(BaseCommand):
    help = (
        "Create idempotent Trainline demo data locally or, with explicit safeguards, "
        "in a new disposable deployment database."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--temporary-deployment-demo",
            action="store_true",
            help=(
                "Allow an explicitly configured production deployment to seed only a new, "
                "isolated synthetic demo database."
            ),
        )

    def handle(self, *args, **options):
        if not settings.ALLOW_DEMO_SEED:
            raise CommandError("Set ALLOW_DEMO_SEED=True to seed a local demo database.")

        production_demo = settings.DJANGO_ENV == "production"
        if production_demo:
            if not options["temporary_deployment_demo"]:
                raise CommandError("Production demo seeding requires --temporary-deployment-demo.")
            if not settings.ALLOW_DEPLOYMENT_DEMO_SEED:
                raise CommandError(
                    "Set ALLOW_DEPLOYMENT_DEMO_SEED=True only for a new disposable demo database."
                )
            if settings.DEMO_USER_PASSWORD == DEVELOPMENT_DEMO_PASSWORD:
                raise CommandError(
                    "Production demo seeding requires a separate DEMO_USER_PASSWORD secret."
                )
            demo_email_domain = settings.DEMO_USER_EMAIL.casefold().rpartition("@")[2]
            if not (
                demo_email_domain == "example.test" or demo_email_domain.endswith(".example.test")
            ):
                raise CommandError(
                    "Production demo seeding requires a synthetic .example.test email address."
                )

        with transaction.atomic():
            if production_demo:
                self._assert_disposable_demo_scope()
            user = self._get_or_create_demo_user()
            passenger = self._get_or_create_passenger(user)
            trips = self._get_or_create_trips()
            self._get_or_create_seats(trips)
            tickets = self._get_or_create_tickets(passenger, trips)
            self._get_or_create_notifications(user, trips)
            self._get_or_create_payments(tickets)
            self._get_or_create_chat_messages(user, tickets)

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
        self.stdout.write(f"Demo username: {user.username}")
        self.stdout.write("Password: value of DEMO_USER_PASSWORD (not printed)")

    def _assert_disposable_demo_scope(self):
        """Refuse to seed a deployment database containing unrelated application data."""
        username = settings.DEMO_USER_USERNAME
        unrelated_data = {
            "users": User.objects.exclude(username=username).exists(),
            "passengers": Passenger.objects.exclude(user__username=username).exists(),
            "trips": TrainTrip.objects.exclude(pk__in=DEMO_TRIP_IDS).exists(),
            "seats": Seat.objects.exclude(train_trip_id__in=DEMO_TRIP_IDS).exists(),
            "tickets": Ticket.objects.exclude(passenger__user__username=username).exists(),
            "notifications": Notification.objects.exclude(user__username=username).exists(),
            "payments": Payment.objects.exclude(payment_id__in=DEMO_PAYMENT_IDS).exists()
            or Payment.objects.filter(payment_id__in=DEMO_PAYMENT_IDS)
            .filter(
                models.Q(ticket__isnull=True)
                | ~models.Q(ticket__passenger__user__username=username)
            )
            .exists(),
            "chat messages": ChatMessage.objects.exclude(chat_id__in=DEMO_CHAT_IDS).exists()
            or ChatMessage.objects.filter(chat_id__in=DEMO_CHAT_IDS)
            .filter(models.Q(user__isnull=True) | ~models.Q(user__username=username))
            .exists(),
        }
        conflicts = [name for name, exists in unrelated_data.items() if exists]
        if conflicts:
            raise CommandError(
                "Refusing to seed a non-disposable database containing unrelated "
                f"application data: {', '.join(conflicts)}. No data was changed."
            )

    def _get_or_create_demo_user(self):
        username = settings.DEMO_USER_USERNAME
        email = settings.DEMO_USER_EMAIL
        existing = User.objects.filter(username=username).first()
        if existing:
            if existing.email.casefold() != email.casefold():
                raise CommandError(
                    "Demo username already belongs to a different email; no user was changed."
                )
            return existing

        if User.objects.filter(email__iexact=email).exists():
            raise CommandError("Demo email already belongs to another user; no user was changed.")

        return User.objects.create_user(
            username=username,
            email=email,
            password=settings.DEMO_USER_PASSWORD,
            first_name="Demo",
            last_name="Traveler",
            passport_number="DEMO-USER-PASSPORT",
        )

    def _get_or_create_passenger(self, user):
        passenger, _ = Passenger.objects.get_or_create(
            user=user,
            defaults={
                "full_name": user.get_full_name(),
                "passport_number": "DEMO-PASSENGER-01",
            },
        )
        return passenger

    def _get_or_create_trips(self):
        definitions = (
            (
                DEMO_TRIP_IDS[0],
                7001,
                "London St Pancras",
                "Paris Gare du Nord",
                datetime(2030, 6, 15, 7, 0, tzinfo=timezone.utc),
                datetime(2030, 6, 15, 9, 20, tzinfo=timezone.utc),
                "Eurostar e320",
                "5",
            ),
            (
                DEMO_TRIP_IDS[1],
                8420,
                "Paris Gare de Lyon",
                "Lyon Part-Dieu",
                datetime(2030, 6, 16, 8, 0, tzinfo=timezone.utc),
                datetime(2030, 6, 16, 10, 0, tzinfo=timezone.utc),
                "TGV Duplex",
                "A",
            ),
            (
                DEMO_TRIP_IDS[2],
                9304,
                "Berlin Hbf",
                "Amsterdam Centraal",
                datetime(2030, 6, 17, 10, 30, tzinfo=timezone.utc),
                datetime(2030, 6, 17, 16, 30, tzinfo=timezone.utc),
                "ICE 3",
                "8",
            ),
        )
        trips = []
        for (
            trip_id,
            service_number,
            origin,
            destination,
            departure,
            arrival,
            consist,
            platform,
        ) in definitions:
            trip, _ = TrainTrip.objects.get_or_create(
                trip_id=trip_id,
                defaults={
                    "service_number": service_number,
                    "origin_station": origin,
                    "destination_station": destination,
                    "departure_time": departure,
                    "arrival_time": arrival,
                    "status": "Scheduled",
                    "consist_type": consist,
                    "platform": platform,
                },
            )
            trips.append(trip)
        return trips

    def _get_or_create_seats(self, trips):
        for trip in trips:
            for row in range(1, 5):
                for column in ("A", "B", "C", "D"):
                    seat_number = f"{row}{column}"
                    if not Seat.objects.filter(train_trip=trip, seat_number=seat_number).exists():
                        Seat.objects.create(
                            train_trip=trip,
                            car_number="1",
                            seat_number=seat_number,
                            travel_class="first" if row == 1 else "standard",
                        )

    def _get_or_create_tickets(self, passenger, trips):
        tickets = []
        definitions = (
            (trips[0], "1A", True, True, True, True, True, "credit_card"),
            (trips[1], "2A", True, False, True, False, False, "cash"),
            (trips[2], None, False, False, False, False, False, None),
        )
        for trip, seat, paid, priority, meal, accommodation, taxi, method in definitions:
            ticket = Ticket.objects.filter(passenger=passenger, train_trip=trip).first()
            if not ticket:
                ticket = Ticket(
                    passenger=passenger,
                    train_trip=trip,
                    seat_num=seat,
                    paid=paid,
                    priority_boarding=priority,
                    meal=meal,
                    accommodation=accommodation,
                    taxi=taxi,
                    payment_method=method,
                )
                ticket.amount = calculate_ticket_amount(ticket)
                ticket.save()
            tickets.append(ticket)
        return tickets

    def _get_or_create_notifications(self, user, trips):
        for trip in trips:
            Notification.objects.get_or_create(
                user=user,
                train_trip=trip,
                message=f"Service {trip.service_number} is scheduled from {trip.origin_station}.",
                defaults={"sent_date": trip.departure_time, "read_status": "unread"},
            )

    def _get_or_create_payments(self, tickets):
        for offset, ticket in enumerate(tickets[:2], start=1):
            Payment.objects.get_or_create(
                payment_id=9000 + offset,
                defaults={
                    "ticket": ticket,
                    "amount": ticket.amount,
                    "currency": "USD",
                    "payment_method": ticket.payment_method,
                    "payment_date": ticket.booked_at,
                    "status": "paid",
                },
            )

    def _get_or_create_chat_messages(self, user, tickets):
        for offset, ticket in enumerate(tickets[:2], start=1):
            ChatMessage.objects.get_or_create(
                chat_id=9000 + offset,
                defaults={
                    "train_trip": ticket.train_trip,
                    "issue_text": "Demo support conversation for this booking.",
                    "created_at": ticket.booked_at,
                    "user": user,
                    "ticket": ticket,
                },
            )
