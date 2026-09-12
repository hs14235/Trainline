from django.db import migrations, models
from django.db.models import Count


def reject_existing_duplicate_seats(apps, schema_editor):
    ticket_model = apps.get_model("core", "Ticket")
    duplicates = list(
        ticket_model.objects.exclude(seat_num__isnull=True)
        .exclude(seat_num="")
        .values("train_trip_id", "seat_num")
        .annotate(total=Count("ticket_id"))
        .filter(total__gt=1)
        .order_by("train_trip_id", "seat_num")[:10]
    )
    if duplicates:
        examples = ", ".join(
            f"trip={item['train_trip_id']} seat={item['seat_num']} count={item['total']}"
            for item in duplicates
        )
        raise RuntimeError(
            "Cannot add the seat uniqueness constraint because duplicate reservations exist. "
            f"Resolve them manually and rerun the migration. Examples: {examples}"
        )


class Migration(migrations.Migration):
    dependencies = [("core", "0002_alter_user_email_alter_user_username")]

    operations = [
        migrations.RunPython(reject_existing_duplicate_seats, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="ticket",
            constraint=models.UniqueConstraint(
                fields=("train_trip", "seat_num"),
                condition=models.Q(seat_num__isnull=False) & ~models.Q(seat_num=""),
                name="uniq_ticket_trip_seat",
            ),
        ),
    ]
