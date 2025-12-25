"""
Example Service 2 - Main Application

Notification service that can optionally consume tasks from Celery queue.
In the POC, notifications are primarily handled by the worker service.
This service provides an API interface for notification management.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from .handlers import get_notification_handler

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting Example Service 2 (Notification Service)")
    logger.info(f"Redis Broker: {os.getenv('REDIS_BROKER_URL', 'NOT_SET')}")
    yield
    logger.info("Shutting down Example Service 2")


# Create FastAPI application
app = FastAPI(
    title="Example Service 2",
    description="Notification Service - Handles notification delivery",
    version="0.1.0",
    lifespan=lifespan,
)


# Health Check Endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "example-service-2",
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "redis_configured": bool(os.getenv("REDIS_BROKER_URL")),
    }


# Notification API Endpoints (placeholder for demonstration)
@app.get("/api/notifications/{notification_id}")
async def get_notification(notification_id: str):
    """Get notification status (placeholder)"""
    logger.info(f"Notification status check for: {notification_id}")
    return {
        "notification_id": notification_id,
        "status": "sent",
        "message": "This is a placeholder. In production, this would query a database.",
    }


@app.post("/api/notifications/send")
async def send_notification_direct(
    recipient: str,
    notification_type: str,
    message: str,
    subject: str = None,
):
    """
    Direct notification send endpoint (alternative to task queue).

    This demonstrates that service-2 can operate independently,
    either consuming tasks from queue OR receiving direct API calls.
    """
    logger.info(f"Direct notification send request: {notification_type} to {recipient}")

    result = get_notification_handler().send_notification_direct(
        recipient=recipient,
        notification_type=notification_type,
        message=message,
        subject=subject,
    )

    return result


if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("SERVICE_PORT", "8000"))
    workers = int(os.getenv("API_WORKERS", "1"))

    logger.info(f"Starting server on {host}:{port} with {workers} workers")
    uvicorn.run(
        "service2.main:app",
        host=host,
        port=port,
        workers=workers,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )