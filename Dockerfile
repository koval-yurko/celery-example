# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY celery_example/ ./celery_example/
COPY .env.example ./.env

# Install Python dependencies
# Using pip to install from pyproject.toml
RUN pip install --no-cache-dir -e .

# Expose any ports if needed (optional, mainly for documentation)
# EXPOSE 5555

# Default command (can be overridden in docker-compose)
CMD ["celery-worker"]