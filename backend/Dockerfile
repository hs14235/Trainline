FROM python:3.10-slim
COPY .env .env

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN echo $DATABASE_URL

WORKDIR /app

COPY requirements.txt .
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --no-cache-dir -r requirements.txt
RUN mkdir -p /app/staticfiles

COPY . .

CMD ["gunicorn", "booking.wsgi:application", "--bind", "0.0.0.0:8000"]
