from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import (
    TrainTrip,    
    Ticket,
    Passenger,
    MembershipLevel,
    Notification,
)

User = get_user_model()

from dj_rest_auth.registration.serializers import RegisterSerializer
class CustomRegisterSerializer(RegisterSerializer):
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name  = serializers.CharField(required=False, allow_blank=True)
    passport_number = serializers.CharField(required=False, allow_blank=True)
    username = serializers.CharField(required=False, allow_blank=True)
    email    = serializers.EmailField(required=True)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['first_name']      = self.validated_data.get('first_name', '')
        data['last_name']       = self.validated_data.get('last_name', '')
        data['passport_number'] = self.validated_data.get('passport_number', '')
        data['membership_level'] = MembershipLevel.objects.get(level_name="Silver")
        data['membership_points'] = 0
        return data


class MembershipLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipLevel
        fields = ['level_name', 'min_points_required']


class UserSerializer(serializers.ModelSerializer):
    membership_level = serializers.StringRelatedField()

    class Meta:
        model = User
        fields = [
            "user_id",
            "first_name",
            "last_name",
            "email",
            "membership_level",
            "membership_points",
        ]
        read_only_fields = ['user_id', 'email', 'membership_points', 'membership_level']



class TrainTripSerializer(serializers.ModelSerializer):
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
  
    train_trip = TrainTripSerializer(read_only=True)

    flight = TrainTripSerializer(source="train_trip", read_only=True)

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
        read_only_fields = ['ticket_id','amount','paid','booked_at']



class PassengerSerializer(serializers.ModelSerializer):
    membership_level = serializers.StringRelatedField()
    class Meta:
        model = Passenger
        fields = ['user','membership_points','membership_level']


class NotificationSerializer(serializers.ModelSerializer):
    train_trip = TrainTripSerializer(read_only=True)

    flight = TrainTripSerializer(source="train_trip", read_only=True)

    class Meta:
        model = Notification
        fields = ['notification_id', 'user', 'train_trip', 'flight', 'message', 'sent_date', 'read_status']
        read_only_fields = ['notification_id', 'sent_date']
