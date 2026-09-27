import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANAGE = ROOT / "backend" / "manage.py"


def production_environment(**overrides):
    environment = os.environ.copy()
    environment.update(
        {
            "DJANGO_ENV": "production",
            "DJANGO_SETTINGS_MODULE": "booking.settings_production",
            "DJANGO_SECRET_KEY": "synthetic-check-only-secret-key-not-for-deployment",
            "DJANGO_DEBUG": "False",
            "ALLOWED_HOSTS": "example.onrender.com",
            "CORS_ALLOWED_ORIGINS": "https://example-frontend.onrender.com",
            "CSRF_TRUSTED_ORIGINS": "https://example-frontend.onrender.com",
            "DATABASE_URL": "sqlite:///:memory:",
            "PAYMENT_MODE": "demo",
        }
    )
    environment.update(overrides)
    return environment


def run_production_check(**overrides):
    return subprocess.run(
        [
            sys.executable,
            str(MANAGE),
            "check",
            "--settings",
            "booking.settings_production",
        ],
        cwd=ROOT,
        env=production_environment(**overrides),
        capture_output=True,
        check=False,
        text=True,
    )


def read_production_setting(expression, **overrides):
    return subprocess.run(
        [
            sys.executable,
            str(MANAGE),
            "shell",
            "--settings",
            "booking.settings_production",
            "-c",
            (
                "from django.conf import settings; "
                "from django.test import RequestFactory; "
                f"print({expression})"
            ),
        ],
        cwd=ROOT,
        env=production_environment(**overrides),
        capture_output=True,
        check=False,
        text=True,
    )


def test_production_settings_accept_debug_false_and_demo_payment_mode():
    result = run_production_check()

    assert result.returncode == 0, result.stderr
    assert "System check identified no issues" in result.stdout


def test_production_settings_fail_closed_when_debug_is_true():
    result = run_production_check(DJANGO_DEBUG="True")

    assert result.returncode != 0
    assert "DJANGO_DEBUG must be False" in result.stderr


def test_runtime_rejects_unimplemented_live_payment_mode():
    result = run_production_check(PAYMENT_MODE="live")

    assert result.returncode != 0
    assert "Only PAYMENT_MODE=demo is implemented" in result.stderr


def test_production_rejects_wildcard_host_and_insecure_browser_origin():
    wildcard_host = run_production_check(ALLOWED_HOSTS="*.onrender.com")
    insecure_origin = run_production_check(CORS_ALLOWED_ORIGINS="http://frontend.example.test")

    assert wildcard_host.returncode != 0
    assert "exact hostnames" in wildcard_host.stderr
    assert insecure_origin.returncode != 0
    assert "exact HTTPS origins" in insecure_origin.stderr


def test_forwarded_protocol_is_trusted_only_when_explicitly_enabled():
    disabled = read_production_setting(
        "getattr(settings, 'SECURE_PROXY_SSL_HEADER', None)", TRUST_X_FORWARDED_PROTO="False"
    )
    enabled = read_production_setting(
        "settings.SECURE_PROXY_SSL_HEADER", TRUST_X_FORWARDED_PROTO="True"
    )

    assert disabled.returncode == 0, disabled.stderr
    assert disabled.stdout.strip().endswith("None")
    assert enabled.returncode == 0, enabled.stderr
    assert "HTTP_X_FORWARDED_PROTO" in enabled.stdout
    assert "https" in enabled.stdout

    insecure_request = read_production_setting(
        "RequestFactory().get('/', HTTP_X_FORWARDED_PROTO='https').is_secure()",
        TRUST_X_FORWARDED_PROTO="False",
    )
    secure_request = read_production_setting(
        "RequestFactory().get('/', HTTP_X_FORWARDED_PROTO='https').is_secure()",
        TRUST_X_FORWARDED_PROTO="True",
    )
    assert insecure_request.stdout.strip().endswith("False")
    assert secure_request.stdout.strip().endswith("True")


def test_cross_origin_credentials_are_disabled_by_default():
    result = read_production_setting("settings.CORS_ALLOW_CREDENTIALS")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().endswith("False")
