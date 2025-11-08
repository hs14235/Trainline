# booking/settings.py
from pathlib import Path
import os
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# ── .env loader ────────────────────────────────────────────────────────────────
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# ── Core ──────────────────────────────────────────────────────────────────────
SECRET_KEY = env("DJANGO_SECRET_KEY")                   # do NOT hardcode
DEBUG = env.bool("DJANGO_DEBUG", False)

ALLOWED_HOSTS = [h.strip() for h in env(
    "ALLOWED_HOSTS",
    default="127.0.0.1,localhost"
).split(",")]

SITE_ID = 1
AUTH_USER_MODEL = "core.User"

# ── Apps ──────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",   # serve static in dev without collectstatic
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

# ── Middleware ────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # static in prod
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

# ── Templates ────────────────────────────────────────────────────────────────
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

# ── Database (reads DATABASE_URL; falls back to sqlite) ───────────────────────
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR/'db.sqlite3'}")
}

# ── Password validators ───────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── i18n / tz ─────────────────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ── Static files ──────────────────────────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ── DRF: schema + auth + throttling ───────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Keep Token+Session for now (you can switch to JWT later)
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
    "DEFAULT_THROTTLE_RATES": {"user": "2000/day"},
}

SPECTACULAR_SETTINGS = {
    "TITLE": env("SPECTACULAR_TITLE", default="Trainline API"),
    "VERSION": env("SPECTACULAR_VERSION", default="1.0.0"),
}

# ── dj-rest-auth / allauth ────────────────────────────────────────────────────
REST_AUTH_REGISTER_SERIALIZERS = {
    "REGISTER_SERIALIZER": "core.serializers.CustomRegisterSerializer",
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

ACCOUNT_LOGIN_METHODS = {"email"}           # was ACCOUNT_AUTHENTICATION_METHOD
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]  # replaces EMAIL_REQUIRED/USERNAME_REQUIRED
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None

# ── CORS / CSRF ───────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [o.strip() for o in env(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000"
).split(",")]
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# ── Basic security (good defaults; prod will set DEBUG=False) ─────────────────
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
