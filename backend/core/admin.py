# core/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import TrainTrip, Ticket, Passenger, MembershipLevel

User = get_user_model()

# Helper for membership_level if it's a FK and nullable
def get_membership_level(obj):
    return obj.membership_level.level_name if obj.membership_level else "-"
get_membership_level.short_description = 'Membership Level'

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email',  'is_active', get_membership_level)
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
        'platform',
    )
    search_fields = ('service_number', 'origin_station', 'destination_station', 'status')
    list_filter = ("status",)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('passenger', 'train_trip', 'paid', 'amount', 'priority_boarding', 'meal', 'booked_at')
    list_filter = ('paid', 'priority_boarding', 'meal')
    search_fields = ('id', 'passenger__user__email', 'train_trip__service_number')

@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = ('user', 'membership_level', 'membership_points')
    search_fields = ('user__email',)

@admin.register(MembershipLevel)
class MembershipLevelAdmin(admin.ModelAdmin):
    list_display = ('level_name', 'min_points_required')
    ordering = ('min_points_required',)
