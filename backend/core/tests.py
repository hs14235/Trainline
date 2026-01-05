from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from .models import TrainTrip, Ticket, Passenger, MembershipLevel
from .membership import update_membership_level

User = get_user_model()

class PaymentAndMembershipTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='t@test.com', username='t', password='pw')
        self.client.force_authenticate(user=self.user)

        # Bronze starter level
        MembershipLevel.objects.create(level_name='Bronze', min_points_required=0)

        self.passenger = Passenger.objects.create(
            user=self.user,
            full_name='Tester',
            passport_number='P12345',
            membership_points=0
        )

        self.trip = TrainTrip.objects.create(
            train_trip_id='T500',
            service_number='TS500',
            origin_station='A',
            destination_station='B',
            departure_time=timezone.now(),
            arrival_time=timezone.now()
        )

    def test_book_full_awards_point_and_updates_level(self):
        # prime passenger to 2 points (one away from Silver)
        self.passenger.membership_points = 2
        self.passenger.save()
        update_membership_level(self.passenger)

        resp = self.client.post(
            f'/api/trips/{self.trip.train_trip_id}/book/',
            {
                'priority_boarding': True,
                'meal': True,
                'accommodation': True,
                'taxi': True
            },
            format='json'
        )

        self.assertEqual(resp.status_code, 201)
        self.passenger.refresh_from_db()
        # awarded one point, now 3 → Silver
        self.assertEqual(self.passenger.membership_points, 3)
        self.assertEqual(self.passenger.membership_level.level_name, 'Silver')

    def test_partial_update_awards_point_when_ticket_becomes_full(self):
        # ticket with one missing add-on
        t = Ticket.objects.create(
            passenger=self.passenger,
            train_trip=self.trip,
            seat_number='3B',
            priority_boarding=True,
            meal=True,
            accommodation=False,
            taxi=True,
            paid=False,
            amount=50
        )

        resp = self.client.patch(f'/api/tickets/{t.pk}/', {'accommodation': True}, format='json')
        self.assertEqual(resp.status_code, 200)

        self.passenger.refresh_from_db()
        # awarded 1 point when it became full
        self.assertEqual(self.passenger.membership_points, 1)
        self.assertIn('membership_points', resp.data)
        self.assertTrue(resp.data['ticket']['accommodation'])

    def test_pay_does_not_override_points_but_returns_level(self):
        # set passenger to Gold via points and ensure level is set
        self.passenger.membership_points = 6
        self.passenger.save()
        update_membership_level(self.passenger)
        self.passenger.refresh_from_db()
        self.assertEqual(self.passenger.membership_level.level_name, 'Gold')

        # create an unpaid ticket (not intended to change points on pay)
        t = Ticket.objects.create(
            passenger=self.passenger,
            train_trip=self.trip,
            seat_number='7C',
            paid=False,
            amount=100
        )

        resp = self.client.post(f'/api/tickets/{t.pk}/pay/', {'payment_method': 'credit_card'}, format='json')
        self.assertEqual(resp.status_code, 200)
        # pay() returns the current membership info (should remain Gold)
        self.assertEqual(resp.data.get('membership_level'), 'Gold')
        self.passenger.refresh_from_db()
        self.assertEqual(self.passenger.membership_points, 6)