# core/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import TrainTrip, Ticket, Passenger, MembershipLevel

User = get_user_model()

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'membership_level')
    search_fields = ('email',)

@admin.register(TrainTrip)
class TrainTripAdmin(admin.ModelAdmin):
    list_display = (
        'service_number',
        'origin_station',
        'destination_station',
        'departure_time',
        'arrival_time',
        'status',          
        'consist_type',   
        'platform',          
    )
    search_fields = ('service_number', 'origin_station', 'destination_station', 'status')
    list_filter = ("status",)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'passenger', 'train_trip', 'paid','amount', 'priority_boarding', 'meal', 'booked_at')
    list_filter  = ('paid', 'priority_boarding', 'meal')
    search_fields= ('ticket_id', 'passenger__user__user_id', 'train_trip_service_number')

@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = ('user', 'membership_level', 'membership_points')
    search_fields = ('user__email',)

@admin.register(MembershipLevel)
class MembershipLevelAdmin(admin.ModelAdmin):
    list_display = ('level_name', 'min_points_required')
    ordering     = ('min_points_required',)
