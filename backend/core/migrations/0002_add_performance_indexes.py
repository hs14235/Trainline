# Generated migration to add database indexes for performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        # Add index on Ticket.paid for faster filtering of unpaid tickets
        migrations.AddIndex(
            model_name='ticket',
            index=models.Index(fields=['paid'], name='ticket_paid_idx'),
        ),
        # Add index on Passenger.membership_points for faster level calculations
        migrations.AddIndex(
            model_name='passenger',
            index=models.Index(fields=['membership_points'], name='passenger_points_idx'),
        ),
        # Add composite index on Passenger user_id for faster user lookups
        migrations.AddIndex(
            model_name='passenger',
            index=models.Index(fields=['user'], name='passenger_user_idx'),
        ),
        # Add index on Notification.is_read for faster filtering
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['is_read'], name='notification_read_idx'),
        ),
        # Add index on Notification.user for faster user notification lookups
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user'], name='notification_user_idx'),
        ),
    ]
