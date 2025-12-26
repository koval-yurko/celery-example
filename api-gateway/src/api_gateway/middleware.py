"""
Request Logging Middleware

Logs all incoming requests with routing decisions for FR-009 compliance.
"""

import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from api_gateway.log_config import get_logger
from api_gateway.routing import match_route


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all requests with timing and routing information.

    Adds X-Request-ID header to responses for tracing.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with logging.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response with X-Request-ID header
        """
        logger = get_logger()

        # Generate request ID
        request_id = str(uuid.uuid4())

        # Start timer
        start_time = time.time()

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Determine target service (if applicable)
        path = str(request.url.path)
        route = match_route(path)
        target_service = route.name if route else "gateway"

        # Log incoming request
        logger.info(
            f"Incoming request: {request.method} {path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": path,
                "target_service": target_service,
                "client_ip": client_ip,
            },
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Log response
        logger.info(
            f"Request completed: {request.method} {path} -> {response.status_code}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": path,
                "target_service": target_service,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
            },
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
