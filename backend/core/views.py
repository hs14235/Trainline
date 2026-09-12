from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, Passenger, Ticket, TrainTrip
from .serializers import NotificationSerializer, TicketSerializer, TrainTripSerializer
from .services import (
    SeatAssignmentError,
    assign_ticket_seat,
    available_seat_numbers,
    calculate_ticket_amount,
)


def parse_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in ("1", "true", "t", "yes", "y", "on")


def passenger_for_user(user):
    passenger, _ = Passenger.objects.get_or_create(
        user=user,
        defaults={
            "full_name": user.get_full_name() or user.username or user.email,
            "passport_number": f"demo-auto-{user.pk}",
        },
    )
    return passenger


class TrainTripViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TrainTrip.objects.all()
    serializer_class = TrainTripSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = TrainTrip.objects.all()
        origin = self.request.query_params.get("origin")
        destination = self.request.query_params.get("destination")
        status_filter = self.request.query_params.get("status")
        ordering = self.request.query_params.get("ordering", "departure_time")

        if origin:
            queryset = queryset.filter(origin_station__icontains=origin.strip())
        if destination:
            queryset = queryset.filter(destination_station__icontains=destination.strip())
        if status_filter:
            queryset = queryset.filter(status__iexact=status_filter.strip())

        allowed_ordering = {
            "departure_time",
            "-departure_time",
            "arrival_time",
            "-arrival_time",
            "service_number",
            "-service_number",
        }
        if ordering not in allowed_ordering:
            ordering = "departure_time"
        return queryset.order_by(ordering, "trip_id")

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def book(self, request, pk=None):
        trip = self.get_object()
        amenity_values = {
            field: parse_bool(request.data.get(field))
            for field in ("priority_boarding", "meal", "accommodation", "taxi")
        }

        with transaction.atomic():
            passenger = passenger_for_user(request.user)
            ticket = Ticket(passenger=passenger, train_trip=trip, **amenity_values)
            ticket.amount = calculate_ticket_amount(ticket)
            ticket.save()

        return Response(
            {"ticket_id": ticket.pk, "amount": float(ticket.amount)},
            status=status.HTTP_201_CREATED,
        )


FlightViewSet = TrainTripViewSet


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Ticket.objects.filter(passenger__user=self.request.user)
            .select_related("passenger", "passenger__membership_level", "train_trip")
            .order_by("-booked_at", "-ticket_id")
        )

    def perform_create(self, serializer):
        passenger = passenger_for_user(self.request.user)
        ticket = serializer.save(passenger=passenger)
        ticket.amount = calculate_ticket_amount(ticket)
        ticket.save(update_fields=["amount"])

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        current_ticket = self.get_object()
        data = request.data.copy()
        seat_was_supplied = "seat_num" in data
        seat_number = data.pop("seat_num", None)

        try:
            with transaction.atomic():
                locked_ticket = Ticket.objects.select_for_update().get(
                    pk=current_ticket.pk,
                    passenger__user=request.user,
                )
                serializer = self.get_serializer(locked_ticket, data=data, partial=partial)
                serializer.is_valid(raise_exception=True)
                ticket = serializer.save()

                new_amount = calculate_ticket_amount(ticket)
                if ticket.amount != new_amount:
                    ticket.amount = new_amount
                    ticket.save(update_fields=["amount"])

                if seat_was_supplied:
                    assign_ticket_seat(ticket=ticket, seat_number=seat_number)
        except SeatAssignmentError as exc:
            response_status = (
                status.HTTP_409_CONFLICT if exc.code == "conflict" else status.HTTP_400_BAD_REQUEST
            )
            return Response({"seat_num": [str(exc)]}, status=response_status)

        return Response(self.get_serializer(ticket).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def pay(self, request, pk=None):
        payment_method = request.data.get("payment_method")
        valid_methods = {choice[0] for choice in Ticket._meta.get_field("payment_method").choices}

        if not payment_method:
            raise ValidationError({"payment_method": "This field is required."})
        if payment_method not in valid_methods:
            raise ValidationError(
                {
                    "payment_method": (
                        "Invalid payment method. Choose one of: " + ", ".join(sorted(valid_methods))
                    )
                }
            )

        with transaction.atomic():
            ticket = get_object_or_404(
                Ticket.objects.select_for_update().select_related("passenger"),
                pk=pk,
                passenger__user=request.user,
            )
            if ticket.paid:
                return Response(
                    {"payment_method": ["Ticket is already paid."]},
                    status=status.HTTP_409_CONFLICT,
                )
            ticket.paid = True
            ticket.payment_method = payment_method
            ticket.save(update_fields=["paid", "payment_method"])
            ticket.passenger.refresh_from_db()

        passenger = ticket.passenger
        return Response(
            {
                "status": "paid",
                "membership_points": passenger.membership_points,
                "membership_level": (
                    passenger.membership_level.level_name
                    if passenger.membership_level
                    else "Bronze"
                ),
            }
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses=inline_serializer(
            name="MeResponse",
            fields={
                "email": serializers.EmailField(),
                "username": serializers.CharField(),
                "first_name": serializers.CharField(),
                "last_name": serializers.CharField(),
                "membership_points": serializers.IntegerField(),
                "membership_level": serializers.CharField(),
            },
        )
    )
    def get(self, request):
        passenger = getattr(request.user, "passenger", None)
        return Response(
            {
                "email": request.user.email,
                "username": request.user.username,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "membership_points": passenger.membership_points if passenger else 0,
                "membership_level": (
                    passenger.membership_level.level_name
                    if passenger and passenger.membership_level
                    else "Bronze"
                ),
            }
        )


class SeatListCreateView(generics.GenericAPIView):
    """List available seats or assign one to the authenticated user's ticket."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=serializers.ListSerializer(child=serializers.CharField()))
    def get(self, request, flight_id):
        trip = get_object_or_404(TrainTrip, pk=flight_id)
        return Response(available_seat_numbers(trip))

    @extend_schema(
        request=inline_serializer(
            name="SeatAssignmentRequest",
            fields={
                "ticket_id": serializers.IntegerField(),
                "seat_num": serializers.CharField(),
            },
        ),
        responses=inline_serializer(
            name="SeatAssignmentResponse",
            fields={
                "status": serializers.CharField(),
                "seat_num": serializers.CharField(),
            },
        ),
    )
    def post(self, request, flight_id):
        ticket_id = request.data.get("ticket_id")
        if ticket_id in (None, ""):
            raise ValidationError({"ticket_id": "This field is required."})

        try:
            ticket_id = int(ticket_id)
        except (TypeError, ValueError):
            raise ValidationError({"ticket_id": "A valid integer is required."})

        ticket = get_object_or_404(
            Ticket.objects.select_related("train_trip"),
            pk=ticket_id,
            passenger__user=request.user,
        )
        if ticket.train_trip_id != str(flight_id):
            raise ValidationError({"ticket_id": "Ticket does not belong to this trip."})

        try:
            assign_ticket_seat(ticket=ticket, seat_number=request.data.get("seat_num"))
        except SeatAssignmentError as exc:
            response_status = (
                status.HTTP_409_CONFLICT if exc.code == "conflict" else status.HTTP_400_BAD_REQUEST
            )
            return Response({"seat_num": [str(exc)]}, status=response_status)

        return Response({"status": "seat assigned", "seat_num": ticket.seat_num})


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).select_related("train_trip")

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.read_status = "read"
        notification.save(update_fields=["read_status"])
        return Response({"status": "ok"})
