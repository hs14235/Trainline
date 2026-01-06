# Generated migration to fix seat_number constraints

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_schema_improvements'),
    ]

    operations = [
        # Make seat_number optional (blank=True, default='')
        migrations.AlterField(
            model_name='ticket',
            name='seat_number',
            field=models.CharField(max_length=10, blank=True, default=''),
        ),
        
        # Remove the old unique_together constraint
        migrations.AlterUniqueTogether(
            name='ticket',
            unique_together=set(),
        ),
        
        # Add partial unique constraint (only when seat_number is not empty)
        migrations.AddConstraint(
            model_name='ticket',
            constraint=models.UniqueConstraint(
                fields=['train_trip', 'seat_number'],
                condition=~models.Q(seat_number=''),
                name='unique_train_seat_when_assigned'
            ),
        ),
    ]
