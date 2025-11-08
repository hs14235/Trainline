from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Ticket, Passenger, MembershipLevel

@receiver([post_save, post_delete], sender=Ticket)
def recalc_membership(sender, instance, **kwargs):
    passenger = instance.passenger

    full_count = Ticket.objects.filter(
        passenger=passenger,
        paid=True,
        priority_boarding=True,
        meal=True,
        accommodation=True,
        taxi=True
    ).count()

    passenger.membership_points = full_count

    if full_count >= 9:
        level_name, defaults = "Platinum", {
            "min_points_required": 20000,
            "perks_description": "Lounge access, extra baggage"
        }
    elif full_count >= 5:
        level_name, defaults = "Gold", {
            "min_points_required": 5000,
            "perks_description": "Free checked bag, priority boarding"
        }
    elif full_count >= 2:
        level_name, defaults = "Silver", {
            "min_points_required": 0,
            "perks_description": "Standard boarding"
        }
    else:
        level_name, defaults = None, {}

    if level_name:
        lvl, _ = MembershipLevel.objects.get_or_create(level_name=level_name, defaults=defaults)
        passenger.membership_level = lvl
    else:
        passenger.membership_level = None

    passenger.save()
