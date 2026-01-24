#!/bin/bash
set -e

# Validate critical environment variables
# Case-insensitive check for production mode
DEBUG_LOWER=$(echo "${DJANGO_DEBUG:-}" | tr '[:upper:]' '[:lower:]')
if [ "$DEBUG_LOWER" = "false" ] || [ "$DEBUG_LOWER" = "0" ]; then
    echo "Production mode detected (DEBUG=$DJANGO_DEBUG)"
    
    # Check if SECRET_KEY is unset, empty, or the default insecure value
    if [ -z "$DJANGO_SECRET_KEY" ] || [ "$DJANGO_SECRET_KEY" = "dev-secret-key-CHANGE-THIS-IN-PRODUCTION" ]; then
        echo "ERROR: Production deployment detected with insecure or missing SECRET_KEY!"
        echo "Please set DJANGO_SECRET_KEY to a secure random value."
        echo "Generate one with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
        exit 1
    fi
    
    # Check SECRET_KEY length
    if [ ${#DJANGO_SECRET_KEY} -lt 50 ]; then
        echo "WARNING: DJANGO_SECRET_KEY should be at least 50 characters long for production"
    fi
    
    echo "✓ Security checks passed"
fi

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn booking.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
