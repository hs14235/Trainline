#!/bin/sh
set -eu

if [ "${DJANGO_ENV:-development}" = "production" ]; then
    if [ -z "${DJANGO_SECRET_KEY:-}" ] || [ "${DJANGO_SECRET_KEY}" = "dev-only-trainline-secret-key-do-not-use-in-production" ]; then
        echo "ERROR: production requires a non-demo DJANGO_SECRET_KEY." >&2
        exit 1
    fi
fi

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "Applying database migrations..."
    python manage.py migrate --noinput
fi

if [ "${COLLECT_STATIC:-false}" = "true" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput --clear
fi

exec "$@"
