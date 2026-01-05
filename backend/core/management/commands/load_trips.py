import csv
from django.core.management.base import BaseCommand
from core.models import TrainTrip
from django.utils.dateparse import parse_datetime

class Command(BaseCommand):
    help = 'Load TrainTrip data from CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        created_count = 0

        with open(csv_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                trip_id = row['train_trip_id']

                trip, created = TrainTrip.objects.get_or_create(
                    train_trip_id=trip_id,
                    defaults={
                        'service_number': row['service_number'],
                        'origin_station': row['origin_station'],
                        'destination_station': row['destination_station'],
                        'departure_time': parse_datetime(row['departure_time']),
                        'arrival_time': parse_datetime(row['arrival_time']),
                        'platform': row.get('platform', ''),
                        'consist_model': row.get('consist_model', ''),
                        'status': row.get('status', 'on_time')
                    }
                )
                if created:
                    created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Loaded {created_count} new trips."))
