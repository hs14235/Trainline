from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    # Your last good migration per the screenshot:
    dependencies = [
        ('core', '0007_alter_notification_options'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                # Rename the historical model (STATE ONLY).
                migrations.RenameModel('Flight', 'TrainTrip'),

                # Point FKs at TrainTrip in STATE, but keep the same DB column.
                migrations.AlterField(
                    model_name='ticket',
                    name='train_trip',
                    field=models.ForeignKey(
                        to='core.traintrip',
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='tickets',
                        db_column='flight_id',
                        null=True,
                        blank=True,
                    ),
                ),
                migrations.AlterField(
                    model_name='notification',
                    name='train_trip',
                    field=models.ForeignKey(
                        to='core.traintrip',
                        on_delete=django.db.models.deletion.CASCADE,
                        db_column='flight_id',
                        null=True,
                        blank=True,
                    ),
                ),
                # If (and only if) your ChatMessage model now has `train_trip`:
                # migrations.AlterField(
                #     model_name='chatmessage',
                #     name='train_trip',
                #     field=models.ForeignKey(
                #         to='core.traintrip',
                #         on_delete=django.db.models.deletion.DO_NOTHING,
                #         db_column='flight_id',
                #         null=True,
                #         blank=True,
                #     ),
                # ),
            ],
        ),
    ]
