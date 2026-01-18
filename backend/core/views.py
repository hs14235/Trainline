from django.utils import timezone       
from requests import request
from rest_framework import status, viewsets, generics, permissions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import TrainTrip, Ticket, Passenger
from .serializers import TrainTripSerializer, TicketSerializer  
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework.views import APIView



class TrainTripViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TrainTrip.objects.all().order_by("departure_time")
    serializer_class = TrainTripSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _parse_bool(v):
        if isinstance(v, bool): return v
        if v is None: return False
        if isinstance(v, (int, float)): return bool(v)
        return str(v).strip().lower() in ("1", "true", "t", "yes", "y", "on")


    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def book(self, request, pk=None):
        trip = self.get_object()
        pb = _parse_bool(request.data.get("priority_boarding"))
        meal = _parse_bool(request.data.get("meal"))
        accom = _parse_bool(request.data.get("accommodation"))
        taxi = _parse_bool(request.data.get("taxi"))
        base_fare = getattr(trip, 'fare', 100)
        amount = base_fare + (50 if pb else 0) + (30 if meal else 0) + (60 if accom else 0) + (40 if taxi else 0)

        passenger, _ = Passenger.objects.get_or_create(
            user=request.user,
            defaults={
                "full_name": request.user.username or request.user.email,
                "passport_number": f"auto-{request.user.pk}",
            },
        )

        ticket = Ticket.objects.create(
            passenger=passenger,
            train_trip=trip,
            priority_boarding=pb,
            meal=meal,
            accommodation=accom,
            taxi=taxi,
            amount=amount,
        )

        return Response(
            {"ticket_id": ticket.pk, "amount": amount},
            status=status.HTTP_201_CREATED
        )


FlightViewSet = TrainTripViewSet


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(passenger__user=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def pay(self, request, pk=None):
        ticket = self.get_object()
        pm = request.data.get("payment_method")
        if not pm:
            return Response({"error": "payment_method required"}, status=400)
        ticket.paid = True
        ticket.payment_method = pm
        ticket.save()
        ticket.passenger.refresh_from_db()
        passenger = ticket.passenger
        return Response({
        "status": "paid",
        "membership_points": passenger.membership_points,
         "membership_level": passenger.membership_level.level_name if passenger.membership_level else "Bronze",
     }, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        passenger = getattr(user, "passenger", None)
        return Response({
            "email": user.email,
            "username": user.username,
            "membership_points": passenger.membership_points if passenger else 0,
            "membership_level": (
                passenger.membership_level.level_name
                if passenger and passenger.membership_level else "Bronze"
            ),
        })


class SeatListCreateView(generics.GenericAPIView):
    """
    GET  /api/seats/<flight_id>/ → list free seats
    POST /api/seats/<flight_id>/ → assign a seat to ticket_id
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, flight_id):
        # TODO: return actual available seats
        all_seats  = ["1A","1B","1C","1D","2A","2B","2C","2D"]
        taken = Ticket.objects.filter(train_trip__trip_id=flight_id).values_list("seat_num", flat=True)
        free_seats = [s for s in all_seats if s not in taken]
        return Response(free_seats)

    def post(self, request, flight_id):
        seat      = request.data.get("seat_num")
        ticket_id = request.data.get("ticket_id")
        ticket    = Ticket.objects.get(pk=ticket_id, passenger__user=request.user)
        ticket.seat_num = seat
        ticket.save(update_fields=["seat_num"])
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
        n.read_status = "read"
        n.save(update_fields=["read_status"])
        return Response({'status': 'ok'})                                                                                                                                                                                                                                                                                                   