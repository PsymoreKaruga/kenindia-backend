# backend/Dockerfile
FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy & install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Collect static (for admin + PDFs)
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# PRODUCTION SERVER
CMD ["gunicorn", "kenindia_backend.wsgi:application", "--bind", "0.0.0.0:8000"]