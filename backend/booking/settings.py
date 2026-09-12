from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")


def csv_env(name, default=""):
    """Return a normalized comma-separated environment setting."""
    return [value.strip() for value in env(name, default=default).split(",") if value.strip()]


DJANGO_ENV = env("DJANGO_ENV", default="development").strip().lower()
DEBUG = env.bool("DJANGO_DEBUG", default=DJANGO_ENV == "development")

# This public local sentinel is intentionally unusable in production.
DEVELOPMENT_SECRET_KEY = "dev-only-trainline-secret-key-do-not-use-in-production"  # nosec B105
SECRET_KEY = env("DJANGO_SECRET_KEY", default=DEVELOPMENT_SECRET_KEY)

ALLOWED_HOSTS = csv_env("ALLOWED_HOSTS", "127.0.0.1,localhost")

if DJANGO_ENV == "production":
    if not SECRET_KEY or SECRET_KEY == DEVELOPMENT_SECRET_KEY or SECRET_KEY.startswith("GENERATE-"):
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must contain a non-demo value when DJANGO_ENV=production."
        )
    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured("ALLOWED_HOSTS must be set when DJANGO_ENV=production.")

SITE_ID = 1
AUTH_USER_MODEL = "core.User"

INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "rest_framework.authtoken",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "core",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "booking.urls"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "booking.wsgi.application"

default_database_url = f"sqlite:///{(BASE_DIR / 'db.sqlite3').as_posix()}"
DATABASES = {"default": env.db("DATABASE_URL", default=default_database_url)}
DATABASES["default"]["CONN_MAX_AGE"] = env.int(
    "DATABASE_CONN_MAX_AGE", default=60 if DJANGO_ENV == "production" else 0
)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"user": env("USER_THROTTLE_RATE", default="2000/day")},
}

SPECTACULAR_SETTINGS = {
    "TITLE": env("SPECTACULAR_TITLE", default="Trainline API"),
    "VERSION": env("SPECTACULAR_VERSION", default="1.0.0"),
}

ACCOUNT_LOGIN_METHODS = {"username"}
ACCOUNT_SIGNUP_FIELDS = ["username*", "email*", "password1*", "password2*"]

REST_AUTH_REGISTER_SERIALIZERS = {
    "REGISTER_SERIALIZER": "core.serializers.CustomRegisterSerializer"
}

CORS_ALLOWED_ORIGINS = csv_env(
    "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
)
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = csv_env(
    "CSRF_TRUSTED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
)

SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=DJANGO_ENV == "production")
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=DJANGO_ENV == "production")
SESSION_COOKIE_HTTPONLY = True
# The CSRF token is not an authentication secret; browser clients must be able
# to read it when using DRF's SessionAuthentication.
CSRF_COOKIE_HTTPONLY = False
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=DJANGO_ENV == "production")
SECURE_HSTS_SECONDS = env.int(
    "SECURE_HSTS_SECONDS", default=31536000 if DJANGO_ENV == "production" else 0
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = DJANGO_ENV == "production"
SECURE_HSTS_PRELOAD = DJANGO_ENV == "production"
X_FRAME_OPTIONS = "DENY"

EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")

ALLOW_DEMO_SEED = env.bool("ALLOW_DEMO_SEED", default=False)
DEMO_USER_USERNAME = env("DEMO_USER_USERNAME", default="demo_traveler")
DEMO_USER_EMAIL = env("DEMO_USER_EMAIL", default="demo.traveler@example.test")
DEMO_USER_PASSWORD = env("DEMO_USER_PASSWORD", default="Trainline-Demo-2026!")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "{asctime} {levelname} {name}: {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": env("DJANGO_LOG_LEVEL", default="INFO"),
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
