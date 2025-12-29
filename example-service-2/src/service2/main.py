"""
Example Service 2 - Main Application

Notification service that can optionally consume tasks from Celery queue.
In the POC, notifications are primarily handled by the worker service.
This service provides an API interface for notification management.
"""

import os
import logging
import uuid
from contextvars import ContextVar
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from .api import router

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Context variable for correlation ID tracking
request_id_context: ContextVar[str] = ContextVar('request_id', default=None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting Example Service 2 (Notification Service)")
    yield
    logger.info("Shutting down Example Service 2")


# Create FastAPI application
app = FastAPI(
    title="Example Service 2",
    description="Notification Service - Handles notification delivery",
    version="0.1.0",
    lifespan=lifespan,
)


# Correlation ID Middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """
    Add correlation ID to all requests for distributed tracing.

    Extracts X-Correlation-ID header if present, or generates a new UUID.
    Sets the correlation ID in context for use in handlers and logging.
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request_id_context.set(correlation_id)

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id

    return response


# Custom Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with standardized error response format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail,
            "details": getattr(exc, "details", None),
            "task_id": getattr(exc, "task_id", None),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with standardized error response."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "details": {"exception": str(exc)},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


# Include API routes
app.include_router(router)


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