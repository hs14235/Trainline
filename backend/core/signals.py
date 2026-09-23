from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Ticket
from .services import recalculate_membership


@receiver([post_save, post_delete], sender=Ticket)
def recalc_membership(sender, instance, **kwargs):
    # Recompute from persisted facts, never increment a counter.
    passenger = getattr(instance, "passenger", None)
    if passenger and type(passenger).objects.filter(pk=passenger.pk).exists():
        with transaction.atomic():
            recalculate_membership(
                passenger,
                event_ticket=instance if kwargs.get("signal") is post_save else None,
            )
