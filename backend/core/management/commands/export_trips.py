import csv
from django.core.management.base import BaseCommand
from core.models import TrainTrip

class Command(BaseCommand):
    help = 'Export TrainTrip data to CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to write the CSV file')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        qs = TrainTrip.objects.all().order_by('train_trip_id')
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'train_trip_id', 'service_number', 'origin_station', 'destination_station',
                'departure_time', 'arrival_time', 'platform', 'consist_model', 'status'
            ])
            writer.writeheader()
            for t in qs:
                writer.writerow({
                    'train_trip_id': t.train_trip_id,
                    'service_number': t.service_number or '',
                    'origin_station': t.origin_station,
                    'destination_station': t.destination_station,
                    'departure_time': t.departure_time.isoformat(),
                    'arrival_time': t.arrival_time.isoformat(),
                    'platform': t.platform or '',
                    'consist_model': t.consist_model or '',
                    'status': t.status or 'on_time',
                })
        self.stdout.write(self.style.SUCCESS(f"Wrote {qs.count()} trips to {csv_file}"))