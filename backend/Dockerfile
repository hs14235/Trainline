FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /app/staticfiles

COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput --clear || true

# Use Gunicorn for production instead of runserver
CMD ["sh", "-c", "python manage.py migrate && gunicorn booking.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60"]
