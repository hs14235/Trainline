FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt
RUN mkdir -p /app/staticfiles

COPY . .

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Use entrypoint script for startup validation and server launch
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "booking.wsgi:application", "--bind=0.0.0.0:8000", "--workers=3", "--timeout=60", "--access-logfile=-", "--error-logfile=-"]
