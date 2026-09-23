from django.db import migrations, models
from django.db.models import Count
import django.db.models.deletion


def reject_duplicate_membership_levels(apps, schema_editor):
    membership_level = apps.get_model("core", "MembershipLevel")
    duplicates = list(
        membership_level.objects.exclude(level_name__isnull=True)
        .values("level_name")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
        .order_by("level_name")
    )
    if duplicates:
        examples = ", ".join(
            f"level={item['level_name']} count={item['total']}" for item in duplicates
        )
        raise RuntimeError(
            "Cannot enforce authoritative membership levels while duplicate names exist. "
            f"Resolve them manually and rerun the migration. Examples: {examples}"
        )


class Migration(migrations.Migration):
    dependencies = [("core", "0003_ticket_unique_trip_seat")]

    operations = [
        migrations.RunPython(
            reject_duplicate_membership_levels,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="membershiplevel",
            name="level_name",
            field=models.CharField(blank=True, max_length=8, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="ticket",
            name="booking_key",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddConstraint(
            model_name="ticket",
            constraint=models.UniqueConstraint(
                fields=("passenger", "booking_key"),
                condition=models.Q(booking_key__isnull=False) & ~models.Q(booking_key=""),
                name="uniq_ticket_passenger_booking_key",
            ),
        ),
        migrations.AddField(model_name="notification", name="event_key", field=models.CharField(blank=True, max_length=100, null=True)),
        migrations.AddField(model_name="notification", name="event_type", field=models.CharField(blank=True, default="general", max_length=24)),
        migrations.AddField(model_name="notification", name="title", field=models.CharField(blank=True, default="Update", max_length=80)),
        migrations.AddField(model_name="notification", name="booking_reference", field=models.CharField(blank=True, default="", max_length=24)),
        migrations.AddField(model_name="notification", name="route_snapshot", field=models.CharField(blank=True, default="", max_length=120)),
        migrations.AddField(model_name="notification", name="seat_snapshot", field=models.CharField(blank=True, default="", max_length=10)),
        migrations.AddField(model_name="notification", name="points_delta", field=models.IntegerField(default=0)),
        migrations.AddField(model_name="notification", name="level_snapshot", field=models.CharField(blank=True, default="", max_length=8)),
        migrations.AddField(model_name="notification", name="is_level_up", field=models.BooleanField(default=False)),
        migrations.AddField(
            model_name="notification",
            name="ticket",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="notifications", to="core.ticket"),
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.UniqueConstraint(
                fields=("user", "event_key"),
                condition=models.Q(event_key__isnull=False) & ~models.Q(event_key=""),
                name="uniq_notification_user_event",
            ),
        ),
    ]
