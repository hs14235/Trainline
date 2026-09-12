import re
from decimal import Decimal

from django.db import transaction

from .models import Seat, Ticket, TrainTrip

DEFAULT_SEAT_NUMBERS = tuple(
    f"{row}{column}" for row in range(1, 9) for column in ("A", "B", "C", "D")
)
SEAT_NUMBER_PATTERN = re.compile(r"^\d{1,2}[A-F]$")
BASE_FARE = Decimal("100.00")
AMENITY_FEES = {
    "priority_boarding": Decimal("50.00"),
    "meal": Decimal("30.00"),
    "accommodation": Decimal("60.00"),
    "taxi": Decimal("40.00"),
}


class SeatAssignmentError(Exception):
    def __init__(self, message, *, code):
        super().__init__(message)
        self.code = code


def calculate_ticket_amount(ticket):
    amount = BASE_FARE
    for field, fee in AMENITY_FEES.items():
        if getattr(ticket, field):
            amount += fee
    return amount


def available_seat_numbers(train_trip):
    configured_seats = list(
        Seat.objects.filter(train_trip=train_trip)
        .order_by("car_number", "seat_number")
        .values_list("seat_number", flat=True)
    )
    seat_numbers = configured_seats or list(DEFAULT_SEAT_NUMBERS)
    taken = set(
        Ticket.objects.filter(train_trip=train_trip)
        .exclude(seat_num__isnull=True)
        .exclude(seat_num="")
        .values_list("seat_num", flat=True)
    )
    return [seat for seat in seat_numbers if seat not in taken]


def normalize_seat_number(value):
    seat_number = str(value or "").strip().upper()
    if not SEAT_NUMBER_PATTERN.fullmatch(seat_number):
        raise SeatAssignmentError(
            "seat_num must be 1-2 digits followed by A-F (for example, 12A)",
            code="invalid",
        )
    return seat_number


def assign_ticket_seat(*, ticket, seat_number):
    """Assign a seat while serializing reservations for the same trip.

    Locking the shared TrainTrip row prevents two requests from observing the
    same unreserved seat concurrently on PostgreSQL, provided all application
    writes use this service.
    """
    seat_number = normalize_seat_number(seat_number)
    if not ticket.train_trip_id:
        raise SeatAssignmentError("Ticket is not associated with a trip", code="invalid")

    with transaction.atomic():
        train_trip = TrainTrip.objects.select_for_update().get(pk=ticket.train_trip_id)
        locked_ticket = Ticket.objects.select_for_update().get(pk=ticket.pk)

        configured_seats = Seat.objects.filter(train_trip=train_trip)
        if (
            configured_seats.exists()
            and not configured_seats.filter(seat_number=seat_number).exists()
        ):
            raise SeatAssignmentError("Seat does not exist for this trip", code="invalid")

        conflict_exists = (
            Ticket.objects.filter(train_trip=train_trip, seat_num=seat_number)
            .exclude(pk=locked_ticket.pk)
            .exists()
        )
        if conflict_exists:
            raise SeatAssignmentError("Seat already taken", code="conflict")

        locked_ticket.seat_num = seat_number
        locked_ticket.save(update_fields=["seat_num"])

    ticket.seat_num = seat_number
    return ticket
