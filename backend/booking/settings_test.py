import os

os.environ.setdefault("DJANGO_ENV", "test")

from .settings import INSTALLED_APPS as BASE_INSTALLED_APPS  # noqa: E402
from .settings import MIDDLEWARE as BASE_MIDDLEWARE  # noqa: E402
from .settings import *  # noqa: E402,F403,F401
from .settings import env  # noqa: E402

INSTALLED_APPS = [app for app in BASE_INSTALLED_APPS if app != "whitenoise.runserver_nostatic"]
MIDDLEWARE = [
    middleware
    for middleware in BASE_MIDDLEWARE
    if middleware != "whitenoise.middleware.WhiteNoiseMiddleware"
]

DATABASES = {"default": env.db("TEST_DATABASE_URL", default="sqlite:///:memory:")}
DATABASES["default"]["CONN_MAX_AGE"] = 0

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
SECURE_SSL_REDIRECT = False
