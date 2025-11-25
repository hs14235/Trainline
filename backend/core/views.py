from django.utils import timezone
from rest_framework import status, viewsets, generics, permissions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import TrainTrip, Flight, Ticket, Passenger, MembershipLevel
from .serializers import TrainTripSerializer, TicketSerializer, UserSerializer
from .models import Notification
from .serializers import NotificationSerializer



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

        ticket = Ticket.objects.create(
            passenger=Passenger.objects.get(user=request.user),
            train_trip=trip,
            priority_boarding=pb,
            meal=meal,
            accommodation=accom,
            taxi=taxi,
            amount=amount,
            booked_at=timezone.now(),
        )

        levels = MembershipLevel.objects.filter(level_name="Bronze")
        if levels.exists():
            bronze_level = levels.first()
        else:
            bronze_level = MembershipLevel.objects.create(
            level_name="Bronze",
            min_points_required=0,
            perks_description="Welcome aboard"
    )


        passenger, created = Passenger.objects.get_or_create(
            user=request.user,
            defaults={'membership_level': bronze_level  }
                )
            
       
        points_earned = (10 if pb else 0) + (5 if meal else 0)
        passenger.membership_points = passenger.membership_points + points_earned
        passenger.save()

        return Response(
            {'ticket_id': ticket.pk, 'amount': amount, 'points_earned': points_earned},
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
        try:
            ticket = self.get_object()
            pm = request.data.get("payment_method")
            if not pm:
                return Response({"error": "payment_method required"}, status=400)

            ticket.paid = True
            ticket.payment_method = pm
            ticket.save()

            passenger = ticket.passenger
            full_count = Ticket.objects.filter(
                passenger=passenger,
                paid=True,
                priority_boarding=True,
                meal=True,
                accommodation=True,
                taxi=True,
            ).count()

            passenger.membership_points = full_count

            if full_count >= 9:
                level_name, defaults = "Platinum", {
                    "min_points_required": 0,
                    "perks_description": "Lounge access, extra baggage",
                }
            elif full_count >= 5:
                level_name, defaults = "Gold", {
                    "min_points_required": 0,
                    "perks_description": "Free checked bag, priority boarding",
                }
            elif full_count >= 2:
                level_name, defaults = "Silver", {
                    "min_points_required": 0,
                    "perks_description": "Standard boarding",
                }
            else:
                level_name = None

            if level_name:
                lvl, _ = MembershipLevel.objects.get_or_create(
                    level_name=level_name,
                    defaults=defaults
                )
                passenger.membership_level = lvl
            else:
                passenger.membership_level = None

            passenger.save()

            user = request.user
            user.membership_points = passenger.membership_points
            user.membership_level = passenger.membership_level
            user.save()

            return Response({
                "status": "paid",
                "full_tickets": full_count,
                "membership_points": passenger.membership_points,
                "membership_level": passenger.membership_level.level_name
                                     if passenger.membership_level else None
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print("🔥 error in pay():", e)
            return Response(
                {"error": "Internal error, see server console"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_update(self, serializer):
        """
        When the user toggles any add‑on (priority_boarding, meal, etc.),
        if it just became “full‑loaded,” award 1 point and bump level.
        """
        ticket = serializer.instance
        old = Ticket.objects.get(pk=ticket.pk)
        serializer.save()  # commit the changes first

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

        if now_full and not was_full:
            passenger = ticket.passenger
            passenger.membership_points = (passenger.membership_points or 0) + 1

            pts = passenger.membership_points
            # bump tier based on total full tickets
            if pts >= 7:
                name, defaults = "Platinum", {"perks_description": "Lounge access, extra baggage"}
            elif pts >= 4:
                name, defaults = "Gold", {"perks_description": "Free checked bag, priority boarding"}
            elif pts >= 2:
                name, defaults = "Silver", {"perks_description": "Standard boarding"}
            else:
                name = "Bronze"
                defaults = {"min_points_required": 0, "perks_description": "Welcome aboard"}

            lvl, _ = MembershipLevel.objects.get_or_create(
                level_name=name,
                defaults=defaults
            )
            passenger.membership_level = lvl
            passenger.save()

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
        # TODO: return actual available seats
        all_seats  = ["1A","1B","1C","1D","2A","2B","2C","2D"]
        taken      = Ticket.objects.filter(flight__flight_id=flight_id).values_list("seat_num", flat=True)
        free_seats = [s for s in all_seats if s not in taken]
        return Response(free_seats)

    def post(self, request, flight_id):
        seat      = request.data.get("seat_num")
        ticket_id = request.data.get("ticket_id")
        ticket    = Ticket.objects.get(pk=ticket_id, passenger__user=request.user)
        ticket.seat_num = seat
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
        n.read_status = 'read'
        n.save()
        return Response({'status': 'ok'})