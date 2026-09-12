import os

os.environ.setdefault("DJANGO_ENV", "production")

from .settings import *  # noqa: E402,F403,F401
