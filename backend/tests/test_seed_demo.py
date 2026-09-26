import pytest
from core.models import (
    ChatMessage,
    Notification,
    Passenger,
    Payment,
    Seat,
    Ticket,
    TrainTrip,
    User,
)
from django.core.management import CommandError, call_command


@pytest.mark.django_db
def test_seed_demo_is_idempotent(settings):
    settings.DJANGO_ENV = "development"
    settings.ALLOW_DEMO_SEED = True
    settings.DEMO_USER_USERNAME = "demo_test_user"
    settings.DEMO_USER_EMAIL = "demo_test_user@example.test"
    settings.DEMO_USER_PASSWORD = "Public-Demo-Pass-12345"

    call_command("seed_demo")
    first_counts = {
        "users": User.objects.count(),
        "trips": TrainTrip.objects.count(),
        "seats": Seat.objects.count(),
        "tickets": Ticket.objects.count(),
        "notifications": Notification.objects.count(),
        "payments": Payment.objects.count(),
        "chat_messages": ChatMessage.objects.count(),
    }
    call_command("seed_demo")

    assert first_counts == {
        "users": 1,
        "trips": 3,
        "seats": 48,
        "tickets": 3,
        "notifications": 6,
        "payments": 2,
        "chat_messages": 2,
    }
    assert first_counts == {
        "users": User.objects.count(),
        "trips": TrainTrip.objects.count(),
        "seats": Seat.objects.count(),
        "tickets": Ticket.objects.count(),
        "notifications": Notification.objects.count(),
        "payments": Payment.objects.count(),
        "chat_messages": ChatMessage.objects.count(),
    }
    assert User.objects.get(username="demo_test_user").check_password("Public-Demo-Pass-12345")

    seeded_models = (User, Passenger, TrainTrip, Seat, Ticket, Notification, Payment)
    for model in seeded_models:
        for instance in model.objects.all():
            for field in model._meta.fields:
                value = getattr(instance, field.attname)
                if field.max_length and isinstance(value, str):
                    assert (
                        len(value) <= field.max_length
                    ), f"{model.__name__}.{field.name} exceeds its database max_length"


@pytest.mark.django_db
def test_seed_demo_requires_explicit_opt_in(settings):
    settings.DJANGO_ENV = "development"
    settings.ALLOW_DEMO_SEED = False
    with pytest.raises(CommandError, match="ALLOW_DEMO_SEED"):
        call_command("seed_demo")


@pytest.mark.django_db
def test_seed_demo_refuses_production(settings):
    settings.DJANGO_ENV = "production"
    settings.ALLOW_DEMO_SEED = True
    settings.ALLOW_DEPLOYMENT_DEMO_SEED = False
    with pytest.raises(CommandError, match="temporary-deployment-demo"):
        call_command("seed_demo")


@pytest.mark.django_db
def test_temporary_production_seed_requires_separate_deployment_opt_in(settings):
    settings.DJANGO_ENV = "production"
    settings.ALLOW_DEMO_SEED = True
    settings.ALLOW_DEPLOYMENT_DEMO_SEED = False

    with pytest.raises(CommandError, match="ALLOW_DEPLOYMENT_DEMO_SEED"):
        call_command("seed_demo", temporary_deployment_demo=True)


@pytest.mark.django_db
def test_temporary_production_seed_requires_synthetic_email_domain(settings):
    settings.DJANGO_ENV = "production"
    settings.ALLOW_DEMO_SEED = True
    settings.ALLOW_DEPLOYMENT_DEMO_SEED = True
    settings.DEMO_USER_EMAIL = "demo@invalid.example.com"
    settings.DEMO_USER_PASSWORD = "Separate-Temporary-Demo-Password-3817"

    with pytest.raises(CommandError, match="synthetic .example.test"):
        call_command("seed_demo", temporary_deployment_demo=True)


@pytest.mark.django_db
def test_seed_demo_allows_only_explicit_isolated_temporary_production_database(settings):
    settings.DJANGO_ENV = "production"
    settings.ALLOW_DEMO_SEED = True
    settings.ALLOW_DEPLOYMENT_DEMO_SEED = True
    settings.DEMO_USER_USERNAME = "temporary_render_demo"
    settings.DEMO_USER_EMAIL = "temporary_render_demo@example.test"
    settings.DEMO_USER_PASSWORD = "Separate-Temporary-Demo-Password-3817"

    call_command("seed_demo", temporary_deployment_demo=True)
    call_command("seed_demo", temporary_deployment_demo=True)

    assert User.objects.filter(username="temporary_render_demo").count() == 1
    assert TrainTrip.objects.count() == 3
    assert Seat.objects.count() == 48
    assert Ticket.objects.count() == 3
    assert Payment.objects.count() == 2


@pytest.mark.django_db
def test_temporary_production_seed_refuses_unrelated_data_without_changes(settings):
    settings.DJANGO_ENV = "production"
    settings.ALLOW_DEMO_SEED = True
    settings.ALLOW_DEPLOYMENT_DEMO_SEED = True
    settings.DEMO_USER_USERNAME = "temporary_render_demo"
    settings.DEMO_USER_EMAIL = "temporary_render_demo@example.test"
    settings.DEMO_USER_PASSWORD = "Separate-Temporary-Demo-Password-3817"
    unrelated = User.objects.create_user(
        username="existing_user",
        email="existing_user@example.test",
        password="Unrelated-User-Password-3817",
    )

    with pytest.raises(CommandError, match="unrelated application data"):
        call_command("seed_demo", temporary_deployment_demo=True)

    assert User.objects.filter(pk=unrelated.pk).exists()
    assert not User.objects.filter(username="temporary_render_demo").exists()
    assert not TrainTrip.objects.exists()


@pytest.mark.django_db
def test_temporary_production_seed_rejects_development_demo_password(settings):
    settings.DJANGO_ENV = "production"
    settings.ALLOW_DEMO_SEED = True
    settings.ALLOW_DEPLOYMENT_DEMO_SEED = True
    settings.DEMO_USER_USERNAME = "temporary_render_demo"
    settings.DEMO_USER_EMAIL = "temporary_render_demo@example.test"
    settings.DEMO_USER_PASSWORD = "Trainline-Demo-2026!"

    with pytest.raises(CommandError, match="separate DEMO_USER_PASSWORD"):
        call_command("seed_demo", temporary_deployment_demo=True)


@pytest.mark.django_db
def test_seed_demo_does_not_overwrite_username_collision(settings):
    settings.DJANGO_ENV = "development"
    settings.ALLOW_DEMO_SEED = True
    settings.DEMO_USER_USERNAME = "existing_user"
    settings.DEMO_USER_EMAIL = "demo@example.test"
    settings.DEMO_USER_PASSWORD = "Public-Demo-Pass-12345"
    existing = User.objects.create_user(
        username="existing_user",
        email="real-person@example.test",
        password="Original-Pass-12345",
    )

    with pytest.raises(CommandError, match="different email"):
        call_command("seed_demo")

    existing.refresh_from_db()
    assert existing.email == "real-person@example.test"
    assert existing.check_password("Original-Pass-12345")
