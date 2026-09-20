import re
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import MembershipLevel, Notification, Seat, Ticket, TrainTrip

DEFAULT_SEAT_NUMBERS = tuple(
    f"{row}{column}" for row in range(1, 9) for column in ("A", "B", "C", "D")
)
SEAT_NUMBER_PATTERN = re.compile(r"^\d{1,2}[A-F]$")
BASE_FARE = Decimal("100.00")
TAXES_AND_FEES = Decimal("0.00")
OPTION_CATALOG = {
    "priority_boarding": {
        "name": "Priority service",
        "description": "Board earlier and earn 1 membership point after payment.",
        "price": Decimal("50.00"),
    },
    "meal": {
        "name": "Onboard meal",
        "description": "Add a meal for your journey.",
        "price": Decimal("30.00"),
    },
    "accommodation": {
        "name": "Accessibility support",
        "description": "Request supported assistance for this journey.",
        "price": Decimal("60.00"),
    },
    "taxi": {
        "name": "Taxi on arrival",
        "description": "Record a local taxi connection in this demo booking.",
        "price": Decimal("40.00"),
    },
}
AMENITY_FEES = {key: value["price"] for key, value in OPTION_CATALOG.items()}
MEMBERSHIP_LEVELS = (
    ("Bronze", 0, "Welcome aboard"),
    ("Silver", 2, "Priority support"),
    ("Gold", 5, "Flexible booking benefits"),
    ("Platinum", 9, "Top-tier traveler benefits"),
)


class SeatAssignmentError(Exception):
    def __init__(self, message, *, code):
        super().__init__(message)
        self.code = code


def money(value):
    return f"{value.quantize(Decimal('0.01')):.2f}"


def quote_for_options(options):
    selected = []
    subtotal = BASE_FARE
    for key, definition in OPTION_CATALOG.items():
        if bool(options.get(key)):
            subtotal += definition["price"]
            selected.append(
                {
                    "key": key,
                    "name": definition["name"],
                    "description": definition["description"],
                    "price": money(definition["price"]),
                }
            )
    return {
        "currency": "USD",
        "base_fare": money(BASE_FARE),
        "options": selected,
        "available_options": [
            {
                "key": key,
                "name": value["name"],
                "description": value["description"],
                "price": money(value["price"]),
            }
            for key, value in OPTION_CATALOG.items()
        ],
        "subtotal": money(subtotal),
        "taxes_and_fees": money(TAXES_AND_FEES),
        "total": money(subtotal + TAXES_AND_FEES),
        "tax_rule": "No taxes or additional fees are applied in this deterministic portfolio demo.",
    }


def quote_for_ticket(ticket):
    return quote_for_options({key: getattr(ticket, key) for key in OPTION_CATALOG})


def calculate_ticket_amount(ticket):
    return Decimal(quote_for_ticket(ticket)["total"])


def seat_inventory(train_trip):
    configured = list(
        Seat.objects.filter(train_trip=train_trip).order_by("car_number", "seat_number")
    )
    seats = configured or [
        Seat(
            train_trip=train_trip,
            car_number="1",
            seat_number=number,
            travel_class="first" if number.startswith("1") else "standard",
        )
        for number in DEFAULT_SEAT_NUMBERS
    ]
    taken = set(
        Ticket.objects.filter(train_trip=train_trip)
        .exclude(seat_num__isnull=True)
        .exclude(seat_num="")
        .values_list("seat_num", flat=True)
    )
    return [
        {
            "seat_number": seat.seat_number,
            "car_number": seat.car_number,
            "travel_class": seat.travel_class,
            "available": seat.seat_number not in taken,
        }
        for seat in seats
    ]


def available_seat_numbers(train_trip):
    return [seat["seat_number"] for seat in seat_inventory(train_trip) if seat["available"]]


def normalize_seat_number(value):
    seat_number = str(value or "").strip().upper()
    if not SEAT_NUMBER_PATTERN.fullmatch(seat_number):
        raise SeatAssignmentError("Choose a valid seat number such as 12A.", code="invalid")
    return seat_number


def ticket_route(ticket):
    if not ticket.train_trip:
        return ""
    origin = ticket.train_trip.origin_station or "Unknown origin"
    destination = ticket.train_trip.destination_station or "Unknown destination"
    return f"{origin} → {destination}"


def create_event_notification(
    *, ticket, event_key, event_type, title, message, seat="", points=0, level="", is_level_up=False
):
    return Notification.objects.get_or_create(
        user=ticket.passenger.user,
        event_key=event_key,
        defaults={
            "event_type": event_type,
            "ticket": ticket,
            "train_trip": ticket.train_trip,
            "title": title,
            "message": message,
            "booking_reference": f"TL-{ticket.ticket_id:06d}",
            "route_snapshot": ticket_route(ticket),
            "seat_snapshot": seat,
            "points_delta": points,
            "level_snapshot": level,
            "is_level_up": is_level_up,
            "sent_date": timezone.now(),
            "read_status": "unread",
        },
    )


def membership_level_for_points(points):
    return next(
        (entry for entry in reversed(MEMBERSHIP_LEVELS) if points >= entry[1]), MEMBERSHIP_LEVELS[0]
    )


def sync_membership_levels():
    levels = {}
    for name, threshold, description in MEMBERSHIP_LEVELS:
        level, _ = MembershipLevel.objects.update_or_create(
            level_name=name,
            defaults={"min_points_required": threshold, "perks_description": description},
        )
        levels[name] = level
    return levels


def ticket_points(ticket):
    if not ticket.paid:
        return 0
    points = 1 if ticket.priority_boarding else 0
    if ticket.seat_num and ticket.train_trip_id:
        points += int(
            Seat.objects.filter(
                train_trip_id=ticket.train_trip_id,
                seat_number=ticket.seat_num,
                travel_class="first",
            ).exists()
        )
    return points


def recalculate_membership(passenger, *, event_ticket=None):
    # Lock only the passenger row. Joining the nullable membership level here
    # produces an outer join that PostgreSQL does not permit with FOR UPDATE.
    passenger = type(passenger).objects.select_for_update().get(pk=passenger.pk)
    previous_points = passenger.membership_points
    previous_level = (
        passenger.membership_level.level_name if passenger.membership_level else "Bronze"
    )
    tickets = Ticket.objects.filter(passenger=passenger).select_related("train_trip")
    points = sum(ticket_points(ticket) for ticket in tickets)
    level_name, _, _ = membership_level_for_points(points)
    level = sync_membership_levels()[level_name]
    passenger.membership_points = points
    passenger.membership_level = level
    passenger.save(update_fields=["membership_points", "membership_level"])
    if event_ticket and points > previous_points:
        priority_delta = int(event_ticket.paid and event_ticket.priority_boarding)
        first_delta = ticket_points(event_ticket) - priority_delta
        if priority_delta:
            create_event_notification(
                ticket=event_ticket,
                event_key=f"points:priority:{event_ticket.pk}",
                event_type="points_awarded",
                title="Priority point earned",
                message="Your paid priority-service booking earned 1 point.",
                points=1,
                level=level_name,
            )
        if first_delta:
            create_event_notification(
                ticket=event_ticket,
                event_key=f"points:first-class:{event_ticket.pk}",
                event_type="points_awarded",
                title="First-class bonus earned",
                message="Your confirmed first-class seat earned 1 bonus point.",
                seat=event_ticket.seat_num or "",
                points=1,
                level=level_name,
            )
        if previous_level != level_name:
            create_event_notification(
                ticket=event_ticket,
                event_key=f"level:{level_name}",
                event_type="level_up",
                title=f"{level_name} unlocked",
                message=f"You reached {level_name} membership.",
                level=level_name,
                is_level_up=True,
            )
    return passenger


def assign_ticket_seat(*, ticket, seat_number):
    """Assign a configured seat while serializing reservations for one trip."""
    seat_number = normalize_seat_number(seat_number)
    if not ticket.train_trip_id:
        raise SeatAssignmentError("Ticket is not associated with a trip.", code="invalid")
    if not ticket.paid:
        raise SeatAssignmentError("Complete demo payment before choosing a seat.", code="invalid")
    with transaction.atomic():
        train_trip = TrainTrip.objects.select_for_update().get(pk=ticket.train_trip_id)
        locked_ticket = (
            Ticket.objects.select_for_update().select_related("passenger__user").get(pk=ticket.pk)
        )
        configured_seats = Seat.objects.filter(train_trip=train_trip)
        if (
            configured_seats.exists()
            and not configured_seats.filter(seat_number=seat_number).exists()
        ):
            raise SeatAssignmentError("That seat is not part of this coach.", code="invalid")
        if (
            Ticket.objects.filter(train_trip=train_trip, seat_num=seat_number)
            .exclude(pk=locked_ticket.pk)
            .exists()
        ):
            raise SeatAssignmentError("That seat was just taken.", code="conflict")
        changed = locked_ticket.seat_num != seat_number
        locked_ticket.seat_num = seat_number
        locked_ticket.save(update_fields=["seat_num"])
        if changed:
            create_event_notification(
                ticket=locked_ticket,
                event_key=f"seat:{locked_ticket.pk}:{seat_number}",
                event_type="seat_confirmed",
                title="Seat confirmed",
                message=f"Seat {seat_number} is confirmed for your journey.",
                seat=seat_number,
            )
        passenger = recalculate_membership(locked_ticket.passenger, event_ticket=locked_ticket)
    ticket.seat_num = seat_number
    ticket.passenger.membership_points = passenger.membership_points
    ticket.passenger.membership_level = passenger.membership_level
    return ticket
