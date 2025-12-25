# Worker Service Dockerfile
# Dedicated Celery worker for task execution
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install common module first
COPY common/pyproject.toml common/
COPY common/src/ common/src/
RUN pip install --no-cache-dir -e ./common

# Copy and install worker service
COPY worker/pyproject.toml worker/
COPY worker/src/ worker/src/
RUN pip install --no-cache-dir -e ./worker

# Set Python path to include worker module
ENV PYTHONPATH=/app/worker/src:$PYTHONPATH

# Create non-root user for security
RUN useradd -m -u 1000 celeryuser && \
    chown -R celeryuser:celeryuser /app

USER celeryuser

# Default environment variables
ENV REDIS_BROKER_URL=redis://redis:6379/0
ENV REDIS_RESULT_BACKEND=redis://redis:6379/1
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from common_tasks.celery_app import celery_app; celery_app.control.inspect().active()" || exit 1

# Start worker
CMD ["python", "-m", "worker.main"]