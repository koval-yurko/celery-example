# Common Module Dockerfile
# Multi-stage build for the shared common_tasks module
FROM python:3.11-slim as builder

WORKDIR /build

# Copy common module files
COPY pyproject.toml ./
COPY src/ ./src/

# Install build dependencies and build wheel
RUN pip install --no-cache-dir build && \
    python -m build --wheel

# Runtime stage (minimal)
FROM python:3.11-slim

WORKDIR /app

# Copy built wheel from builder
COPY --from=builder /build/dist/*.whl /tmp/

# Install the common module
RUN pip install --no-cache-dir /tmp/*.whl && \
    rm -rf /tmp/*.whl

# This image is not meant to be run directly,
# but other services will use it as a base or install from it
CMD ["python", "-c", "import common_tasks; print('Common module installed successfully')"]