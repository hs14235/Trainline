from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

### ------------------------
### USER MANAGEMENT
### ------------------------


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be provided")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)  # ⬅ removed default="user"

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]  # ⬅ so createsuperuser will ask for username too

    class Meta:
        db_table = "core_user"

    def __str__(self):
        return self.email



### ------------------------
### MEMBERSHIP + PASSENGERS
### ------------------------

class MembershipLevel(models.Model):
    level_name = models.CharField(max_length=16)
    min_points_required = models.IntegerField()
    perks_description = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'membership_level'

    def __str__(self):
        return self.level_name


class Passenger(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=20, blank=True, null=True)
    passport_number = models.CharField(max_length=20, unique=True)

    membership_level = models.ForeignKey(MembershipLevel, on_delete=models.PROTECT, null=True, blank=True)
    membership_points = models.IntegerField(default=0)

    class Meta:
        db_table = 'passenger'

    def __str__(self):
        return self.full_name


### ------------------------
### TRAIN TRIPS + SEATS
### ------------------------

class TrainTrip(models.Model):
    train_trip_id = models.CharField(max_length=10, primary_key=True)
    service_number = models.CharField(max_length=10, blank=True, null=True)
    origin_station = models.CharField(max_length=50)
    destination_station = models.CharField(max_length=50)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    consist_model = models.CharField(max_length=50, blank=True, null=True)
    platform = models.CharField(max_length=25, blank=True, null=True)

    STATUS_CHOICES = [('on_time', 'On Time'), ('delayed', 'Delayed'), ('cancelled', 'Cancelled')]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='on_time')

    class Meta:
        db_table = 'train_trip'

    def __str__(self):
        return f"{self.service_number} ({self.origin_station} → {self.destination_station})"


class Seat(models.Model):
    train_trip = models.ForeignKey(TrainTrip, on_delete=models.CASCADE, related_name="seats")
    car_number = models.CharField(max_length=4)
    seat_number = models.CharField(max_length=6)

    CLASS_CHOICES = [('standard', 'Standard'), ('first', 'First'), ('sleeper', 'Sleeper')]
    travel_class = models.CharField(max_length=16, choices=CLASS_CHOICES)

    class Meta:
        db_table = 'seat'
        unique_together = ('train_trip', 'car_number', 'seat_number')


### ------------------------
### TICKETS + PAYMENT
### ------------------------

class Ticket(models.Model):
    passenger = models.ForeignKey(Passenger, on_delete=models.CASCADE)
    train_trip = models.ForeignKey(TrainTrip, on_delete=models.CASCADE, related_name="tickets")
    booked_at = models.DateTimeField(auto_now_add=True)

    seat_number = models.CharField(max_length=10)
    paid = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    PAYMENT_METHODS = [('credit_card', 'Credit Card'), ('cash', 'Cash'), ('check', 'Check')]
    payment_method = models.CharField(max_length=12, choices=PAYMENT_METHODS, null=True, blank=True)

    # Add-on options
    priority_boarding = models.BooleanField(default=False)
    meal = models.BooleanField(default=False)
    accommodation = models.BooleanField(default=False)
    taxi = models.BooleanField(default=False)

    class Meta:
        db_table = 'ticket'


class Payment(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3)
    payment_method = models.CharField(max_length=25)
    payment_date = models.DateTimeField(auto_now_add=True)

    STATUS_CHOICES = [('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        db_table = 'payment'


### ------------------------
### NOTIFICATIONS + CHAT
### ------------------------

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    train_trip = models.ForeignKey(TrainTrip, on_delete=models.CASCADE, null=True, blank=True)
    message = models.CharField(max_length=255)
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'notification'


class ChatMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ticket = models.ForeignKey(Ticket, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_message'
