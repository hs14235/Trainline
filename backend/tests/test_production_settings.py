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
