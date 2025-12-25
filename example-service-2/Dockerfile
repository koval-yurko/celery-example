# Example Service 2 Dockerfile
# Notification Service
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

# Copy and install service
COPY example-service-2/pyproject.toml example-service-2/
COPY example-service-2/src/ example-service-2/src/
RUN pip install --no-cache-dir -e ./example-service-2

# Set Python path
ENV PYTHONPATH=/app/example-service-2/src:$PYTHONPATH

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Default environment variables
ENV REDIS_BROKER_URL=redis://redis:6379/0
ENV REDIS_RESULT_BACKEND=redis://redis:6379/1
ENV SERVICE_PORT=8000
ENV LOG_LEVEL=INFO

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Start service
CMD ["python", "-m", "service2.main"]