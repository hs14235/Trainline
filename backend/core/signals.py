from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Ticket
from .membership import update_membership_level

@receiver([post_save, post_delete], sender=Ticket)
def recalc_membership(sender, instance, **kwargs):
    passenger = instance.passenger
    # re-evaluate level from current points (safe to call even if nothing changed)
    update_membership_level(passenger)