FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /app/staticfiles

# Copy application code
COPY . .

# Create entrypoint script to wait for DB and run migrations
RUN echo '#!/bin/sh\n\
echo "Waiting for database..."\n\
python << END\n\
import socket\n\
import time\n\
import sys\n\
\n\
def wait_for_db(host="db", port=5432, timeout=30):\n\
    start = time.time()\n\
    while time.time() - start < timeout:\n\
        try:\n\
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n\
            sock.settimeout(1)\n\
            sock.connect((host, port))\n\
            sock.close()\n\
            return True\n\
        except (socket.error, socket.timeout):\n\
            time.sleep(0.5)\n\
    return False\n\
\n\
if not wait_for_db():\n\
    print("Database connection timeout!")\n\
    sys.exit(1)\n\
print("Database is ready!")\n\
END\n\
\n\
echo "Running migrations..."\n\
python manage.py migrate --noinput\n\
\n\
echo "Starting server..."\n\
exec python manage.py runserver 0.0.0.0:8000\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
