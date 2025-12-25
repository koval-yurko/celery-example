"""
Example Service 1 - Main Application

Order processing service that publishes orders to Celery task queue.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from .api import router

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting Example Service 1 (Order Processing Service)")
    logger.info(f"Redis Broker: {os.getenv('REDIS_BROKER_URL', 'NOT_SET')}")
    yield
    logger.info("Shutting down Example Service 1")


# Create FastAPI application
app = FastAPI(
    title="Example Service 1",
    description="Order Processing Service - Publishes orders to Celery task queue",
    version="0.1.0",
    lifespan=lifespan,
)

# Include API routes
app.include_router(router)


if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("SERVICE_PORT", "8000"))
    workers = int(os.getenv("API_WORKERS", "1"))

    logger.info(f"Starting server on {host}:{port} with {workers} workers")
    uvicorn.run(
        "service1.main:app",
        host=host,
        port=port,
        workers=workers,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )