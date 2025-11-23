# Use an official Python image as a base
FROM python:3.11-slim

# Set environment variables for Python (no buffer for logs, and no prompts during install)
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set working directory in container
WORKDIR /app

# Install system dependencies (for example, for PostgreSQL client and any other needs)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy requirement files and install Python dependencies
# (If you have a requirements.txt, use that. Otherwise, see below on how to create one)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application code into the container
COPY . .

# Collect static files (Django) – this command makes static files ready for production
RUN python manage.py collectstatic --noinput

# Expose the port (Render will use its own mapping, but this is good practice)
EXPOSE 8000

# Run database migrations (optional: you might run this separately on Render)
# RUN python manage.py migrate

# Start the Django app with Gunicorn (a production-ready web server for Django)
CMD gunicorn booking.wsgi:application --bind 0.0.0.0:8000
