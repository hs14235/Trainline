from django.conf import settings
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)

class TrainTrip(models.Model):
    trip_id = models.CharField(primary_key=True, max_length=10, db_column="flight_id")

    service_number    = models.IntegerField(blank=True, null=True, db_column="flight_number")
    origin_station    = models.CharField(max_length=50, blank=True, null=True, db_column="departure_airport")
    destination_station = models.CharField(max_length=50, blank=True, null=True, db_column="arrival_airport")
    departure_time    = models.DateTimeField(blank=True, null=True)
    arrival_time      = models.DateTimeField(blank=True, null=True)
    status            = models.CharField(max_length=9, blank=True, null=True)

    consist_type      = models.CharField(max_length=50, blank=True, null=True, db_column="aircraft_type")
    platform          = models.CharField(max_length=25, blank=True, null=True, db_column="gate")

    class Meta:
        db_table = 'flight' 
Flight = TrainTrip

class MembershipLevel(models.Model):
    level_name = models.CharField(max_length=8, blank=True, null=True)
    min_points_required = models.IntegerField(blank=True, null=True)
    perks_description = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.level_name or "<unnamed level>"

    class Meta:
        db_table = 'membership_level'

class Passenger(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
          on_delete=models.CASCADE)
    
    relationship = models.CharField(max_length=10, blank=True, null=True)
    
    user = models.OneToOneField('User', models.DO_NOTHING, primary_key=True)
    
    membership_level = models.ForeignKey(
        MembershipLevel,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    passport_number = models.CharField(max_length=20, unique=True)

    membership_points = models.IntegerField(default=0)

    
    class Meta:
        db_table = 'passenger'

class Seat(models.Model):
    train_trip = models.ForeignKey(TrainTrip, on_delete=models.CASCADE, related_name="seats")
    car_number = models.CharField(max_length=4)  
    seat_number = models.CharField(max_length=6)
    travel_class = models.CharField(max_length=16, choices=[("standard","Standard"),("first","First"),("sleeper","Sleeper")])

class Ticket(models.Model):
    ticket_id   = models.AutoField(primary_key=True)
    passenger   = models.ForeignKey(Passenger, on_delete=models.CASCADE)

    train_trip  = models.ForeignKey(
        TrainTrip,
        on_delete=models.CASCADE,
        related_name="tickets",
        db_column="flight_id",     
        null=True,                 
        blank=True,
    )

    booked_at   = models.DateTimeField(auto_now_add=True)
    seat_num    = models.CharField(max_length=10, blank=True, null=True)
    paid        = models.BooleanField(default=False)
    amount      = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    payment_method = models.CharField(
        max_length=12,
        choices=[('credit_card','Credit Card'), ('check','Check'), ('cash','Cash')],
        blank=True, null=True
    )

    priority_boarding = models.BooleanField(default=False)
    meal        = models.BooleanField(default=False)
    accommodation = models.BooleanField(default=False)
    taxi        = models.BooleanField(default=False)

    class Meta:
        db_table = 'ticket'

class Notification(models.Model):
    notification_id = models.AutoField(primary_key=True)

    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    train_trip = models.ForeignKey(
    TrainTrip,
    on_delete=models.CASCADE,
    null=True, blank=True,
    db_column="flight_id"     
)
    message     = models.CharField(max_length=255)
    sent_date       = models.DateTimeField(null=True, blank=True)
    read_status     = models.CharField(max_length=6, null=True, blank=True)

    class Meta:
        db_table = 'notification'


class Payment(models.Model):
    payment_id = models.IntegerField(primary_key=True)
    ticket = models.ForeignKey(Ticket, models.DO_NOTHING, blank=True, null=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, blank=True, null=True)
    payment_method = models.CharField(max_length=25, blank=True, null=True)
    payment_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=7, blank=True, null=True)

    class Meta:
        db_table = 'payment'


from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, user_id, email, password=None, **extra_fields):
        if not user_id:
            raise ValueError("`user_id` must be set")
        email = self.normalize_email(email)
        user = self.model(user_id=user_id, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_id, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(user_id, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    user_id          = models.CharField(max_length=10, primary_key=True)
    passport_number = models.CharField(max_length=20, unique=True)
    passport_number = models.CharField(
        max_length=20,
        unique=False,        
        blank=True,         
        null=True,         
        default=None,
    )
    email            = models.CharField(max_length=75, unique=True)
    first_name       = models.CharField(max_length=32)
    last_name        = models.CharField(max_length=50, blank=True)
    membership_level = models.ForeignKey(
        'MembershipLevel',
        null=True, blank=True,
        on_delete=models.SET_NULL
    )
    membership_points = models.IntegerField(default=0)

    is_active    = models.BooleanField(default=True)
    is_staff     = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    last_login   = models.DateTimeField(null=True, blank=True)
    date_joined  = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD  = 'user_id'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    class Meta:
        db_table = 'user'  


class ChatMessage(models.Model):
    train_trip = models.ForeignKey(
    TrainTrip,
    models.DO_NOTHING,
    blank=True, null=True,
    db_column="flight_id"     
    )
    chat_id = models.IntegerField(primary_key=True)
    issue_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    user = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    
    ticket = models.ForeignKey(Ticket, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        db_table = 'chat_message'
