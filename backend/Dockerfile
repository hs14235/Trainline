FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /app/staticfiles

COPY . .

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Use entrypoint script for startup validation and server launch
ENTRYPOINT ["/app/entrypoint.sh"]
