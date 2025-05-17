FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=UTC

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for uploads and logs
RUN mkdir -p /app/uploads /app/logs

# Copy application code
COPY . .

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser /app
USER appuser

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]