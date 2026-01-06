# Generated migration for schema improvements

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_performance_indexes'),
    ]

    operations = [
        # Add unique constraint to MembershipLevel.level_name
        migrations.AlterField(
            model_name='membershiplevel',
            name='level_name',
            field=models.CharField(max_length=16, unique=True),
        ),
        
        # Add check constraint for non-negative membership points
        migrations.AddConstraint(
            model_name='passenger',
            constraint=models.CheckConstraint(
                check=models.Q(membership_points__gte=0),
                name='passenger_points_non_negative'
            ),
        ),
        
        # Add indexes on TrainTrip for better query performance
        migrations.AddIndex(
            model_name='traintrip',
            index=models.Index(fields=['departure_time'], name='traintrip_departure_idx'),
        ),
        migrations.AddIndex(
            model_name='traintrip',
            index=models.Index(fields=['status'], name='traintrip_status_idx'),
        ),
        
        # Add unique constraint on Ticket to prevent double-booking same seat
        migrations.AlterUniqueTogether(
            name='ticket',
            unique_together={('train_trip', 'seat_number')},
        ),
        
        # Add check constraint for non-negative ticket amounts
        migrations.AddConstraint(
            model_name='ticket',
            constraint=models.CheckConstraint(
                check=models.Q(amount__gte=0),
                name='ticket_amount_non_negative'
            ),
        ),
    ]
