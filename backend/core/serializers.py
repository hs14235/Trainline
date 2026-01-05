from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer

from django.contrib.auth import get_user_model
from .models import (
    TrainTrip,
    Ticket,
    Passenger,
    MembershipLevel,
    Notification,
)

User = get_user_model()


class SimpleRegisterSerializer(RegisterSerializer):
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)

    def get_cleaned_data(self):
        return {
            "username": self.validated_data.get("username", ""),
            "email": self.validated_data.get("email", ""),
            "password1": self.validated_data.get("password1", ""),
            "password2": self.validated_data.get("password2", ""),
        }


class MembershipLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipLevel
        fields = ['level_name', 'min_points_required']


class UserSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='pk', read_only=True)
    membership_level = serializers.SerializerMethodField()
    membership_points = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "user_id",
            "email",
            "membership_level",
            "membership_points",
        ]
        read_only_fields = ['user_id', 'email', 'membership_points', 'membership_level']

    def get_membership_level(self, obj):
        p = Passenger.objects.filter(user=obj).first()
        return p.membership_level.level_name if p and p.membership_level else None

    def get_membership_points(self, obj):
        p = Passenger.objects.filter(user=obj).first()
        return p.membership_points if p else 0


class TrainTripSerializer(serializers.ModelSerializer):
    # API-friendly aliases for frontend compatibility
    trip_id = serializers.CharField(source='train_trip_id', read_only=True)
    consist_type = serializers.CharField(source='consist_model', read_only=True, allow_null=True)

    class Meta:
        model = TrainTrip
        fields = [
            "trip_id",
            "service_number",
            "origin_station",
            "destination_station",
            "departure_time",
            "arrival_time",
            "status",
            "consist_type",
            "platform",
        ]


FlightSerializer = TrainTripSerializer


class TicketSerializer(serializers.ModelSerializer):
    ticket_id = serializers.IntegerField(source='pk', read_only=True)
    train_trip = TrainTripSerializer(read_only=True)
    flight = TrainTripSerializer(source="train_trip", read_only=True)  # alias kept for compatibility
    # allow client to write seat via 'seat_num' (maps to seat_number)
    seat_num = serializers.CharField(source='seat_number', required=False, allow_null=True)

    class Meta:
        model = Ticket
        fields = [
            'ticket_id',
            'passenger',
            'train_trip',
            'flight',
            'seat_num',
            'priority_boarding',
            'meal',
            'accommodation',
            'taxi',
            'amount',
            'booked_at',
            'paid',
            'payment_method',
        ]
        read_only_fields = ['ticket_id', 'amount', 'paid', 'booked_at']


class PassengerSerializer(serializers.ModelSerializer):
    membership_level = serializers.StringRelatedField()

    class Meta:
        model = Passenger
        fields = ['user', 'membership_points', 'membership_level']


class NotificationSerializer(serializers.ModelSerializer):
    train_trip = TrainTripSerializer(read_only=True)
    flight = TrainTripSerializer(source="train_trip", read_only=True)
    sent_date = serializers.DateTimeField(source='sent_at', read_only=True)
    read_status = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['notification_id', 'user', 'train_trip', 'flight', 'message', 'sent_date', 'read_status']
        read_only_fields = ['notification_id', 'sent_date']

    def get_read_status(self, obj):
        return 'read' if obj.is_read else 'unread'