FROM python:3.11-slim

WORKDIR /app

# Copy and install service
COPY api-gateway/pyproject.toml api-gateway/
COPY api-gateway/src/ api-gateway/src/
RUN pip install --no-cache-dir -e ./api-gateway

# Set Python path
ENV PYTHONPATH=/app/api-gateway/src:$PYTHONPATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Start service
CMD ["python", "-m", "api_gateway.main"]
