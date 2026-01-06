from django.utils import timezone
from rest_framework import status, viewsets, generics, permissions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import TrainTrip, Ticket, Passenger, MembershipLevel
from .serializers import TrainTripSerializer, TicketSerializer, UserSerializer
from .models import Notification
from .serializers import NotificationSerializer
from .membership import update_membership_level


class TrainTripViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TrainTrip.objects.all().order_by("departure_time")
    serializer_class = TrainTripSerializer
    permission_classes = [permissions.IsAuthenticated]


    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def book(self, request, pk=None):
        trip = self.get_object()
        pb   = bool(request.data.get('priority_boarding'))
        meal = bool(request.data.get('meal'))
        accom = bool(request.data.get('accommodation'))
        taxi = bool(request.data.get('taxi'))

        base_fare = getattr(trip, 'fare', 100)
        amount = (
            base_fare +
             (50 if pb else 0) +
             (30 if meal else 0) +
             (60 if accom else 0) +
             (40 if taxi else 0)
        )
        # Ensure Bronze level exists
        bronze_level, _ = MembershipLevel.objects.get_or_create(
            level_name="Bronze",
            defaults={"min_points_required": 0, "perks_description": "Welcome aboard"},
        )

        # Ensure passenger exists for demo: auto-create a minimal profile if missing
        passenger, created = Passenger.objects.get_or_create(
            user=request.user,
            defaults={
                'full_name': getattr(request.user, 'username', request.user.email),
                'passport_number': f"auto-{request.user.pk}",
                'membership_level': bronze_level,
            }
        )

        ticket = Ticket.objects.create(
            passenger=passenger,
            train_trip=trip,
            priority_boarding=pb,
            meal=meal,
            accommodation=accom,
            taxi=taxi,
            amount=amount,
            booked_at=timezone.now(),
        )

        # Award a single point if the ticket is created fully-loaded
        points_earned = 1 if (pb and meal and accom and taxi) else 0
        if points_earned:
            passenger.membership_points = (passenger.membership_points or 0) + points_earned
            update_membership_level(passenger)
            # Note: update_membership_level() already calls passenger.save()

        return Response(
            {
                'ticket_id': ticket.pk,
                'amount': amount,
                'points_earned': points_earned,
                "membership_points": passenger.membership_points,
                "membership_level": passenger.membership_level.level_name if passenger.membership_level else None,
            },
            status=status.HTTP_201_CREATED
        )

FlightViewSet = TrainTripViewSet

from .models import Ticket, MembershipLevel
from .serializers import TicketSerializer

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(passenger__user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def pay(self, request, pk=None):
        """Mark ticket as paid and return current membership info (points-driven)."""
        try:
            ticket = self.get_object()
            pm = request.data.get("payment_method")
            if not pm:
                return Response({"error": "payment_method required"}, status=400)

            ticket.paid = True
            ticket.payment_method = pm
            ticket.save()

            passenger = ticket.passenger
            # Ensure the passenger's level matches their points (safe no-op)
            update_membership_level(passenger)

            return Response({
                "status": "paid",
                "membership_points": passenger.membership_points,
                "membership_level": passenger.membership_level.level_name if passenger.membership_level else None
            }, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            print("error in pay() method:", e)
            print(traceback.format_exc())
            return Response({"error": "Internal error, see server console"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, pk=None):
        """
        Handle PATCH updates to a ticket and return the updated ticket
        plus passenger membership info for immediate frontend refresh.
        """
        ticket = self.get_object()
        serializer = self.get_serializer(ticket, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # ensure we have the latest DB state
        ticket.refresh_from_db()
        passenger = ticket.passenger

        return Response({
            "ticket": serializer.data,
            "membership_points": passenger.membership_points,
            "membership_level": passenger.membership_level.level_name if passenger.membership_level else None
        }, status=status.HTTP_200_OK)


    def perform_update(self, serializer):
        """
        When the user toggles any add‑on (priority_boarding, meal, etc.),
        if it just became “full‑loaded,” award 1 point and bump level.
        """
        ticket = serializer.instance
        old = Ticket.objects.get(pk=ticket.pk)
        serializer.save()  # commit the changes first

        # ensure serializer.instance is up to date
        serializer.instance.refresh_from_db()

        now_full = all([
            serializer.instance.priority_boarding,
            serializer.instance.meal,
            serializer.instance.accommodation,
            serializer.instance.taxi,
        ])
        was_full = all([
            old.priority_boarding,
            old.meal,
            old.accommodation,
            old.taxi,
        ])

        # logging to help debug in container logs
        print(f"[ticket-update] ticket={ticket.pk} now_full={now_full} was_full={was_full}")

        if now_full and not was_full:
            passenger = ticket.passenger
            passenger.membership_points = (passenger.membership_points or 0) + 1
            update_membership_level(passenger)
            

            print(f"[ticket-update] awarded +1 point to passenger={passenger.pk}; total_points={passenger.membership_points}")

class UserDetailView(generics.RetrieveAPIView):
    """
    /api/user/ → returns the serialized User (with those extra profile fields).
    """
    serializer_class   = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class SeatListCreateView(generics.GenericAPIView):
    """
    GET  /api/seats/<flight_id>/ → list free seats
    POST /api/seats/<flight_id>/ → assign a seat to ticket_id
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, flight_id):
        all_seats = ["1A", "1B", "1C", "1D", "2A", "2B", "2C", "2D"]
        taken = Ticket.objects.filter(train_trip__train_trip_id=flight_id).values_list("seat_number", flat=True)
        free_seats = [s for s in all_seats if s not in taken]
        return Response(free_seats)

    def post(self, request, flight_id):
        seat = request.data.get("seat_num") or request.data.get("seat_number")
        ticket_id = request.data.get("ticket_id")
        ticket = Ticket.objects.get(pk=ticket_id, passenger__user=request.user)
        ticket.seat_number = seat
        ticket.save()
        return Response({"status": "seat assigned"})

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        n = self.get_object()
        n.is_read = True
        n.save()
        return Response({'status': 'ok'})