"""
HTTP Proxy Module

Handles request forwarding to backend services using httpx.
"""

import time
from typing import Optional

import httpx
from fastapi import Request
from fastapi.responses import StreamingResponse

from api_gateway.config import ServiceRoute, load_config
from api_gateway.log_config import get_logger

# Headers to strip when forwarding (hop-by-hop headers per RFC 7230)
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "transfer-encoding",
    "te",
    "trailer",
    "upgrade",
    "proxy-authorization",
    "proxy-authenticate",
}


def forward_headers(
    headers: dict, client_ip: str, original_host: str
) -> dict[str, str]:
    """
    Prepare headers for forwarding to backend service.

    Strips hop-by-hop headers and adds X-Forwarded-* headers.

    Args:
        headers: Original request headers
        client_ip: Client IP address
        original_host: Original Host header value

    Returns:
        Filtered headers with X-Forwarded-* additions
    """
    forwarded_headers = {}

    for key, value in headers.items():
        if key.lower() not in HOP_BY_HOP_HEADERS:
            forwarded_headers[key] = value

    # Add X-Forwarded-* headers
    forwarded_headers["X-Forwarded-For"] = client_ip
    forwarded_headers["X-Forwarded-Proto"] = "http"
    forwarded_headers["X-Forwarded-Host"] = original_host

    return forwarded_headers


def rewrite_path(path: str, route: ServiceRoute) -> str:
    """
    Rewrite the request path by stripping the service prefix.

    Example: /api/service1/orders -> /api/orders

    Args:
        path: Original request path
        route: Matched service route

    Returns:
        Rewritten path for backend service
    """
    if route.strip_prefix and path.startswith(route.prefix):
        # Strip the service prefix, keep /api prefix
        remaining = path[len(route.prefix) :]
        return f"/api{remaining}" if remaining else "/api"
    return path


async def proxy_request(
    request: Request,
    route: ServiceRoute,
    target_path: str,
    request_id: str,
) -> StreamingResponse:
    """
    Forward a request to the backend service.

    Args:
        request: Incoming FastAPI request
        route: Matched service route
        target_path: Rewritten target path
        request_id: Request ID for tracing

    Returns:
        StreamingResponse with backend response

    Raises:
        httpx.ConnectError: Backend service unreachable
        httpx.TimeoutException: Backend request timed out
    """
    logger = get_logger()
    config = load_config()

    # Build target URL
    target_url = f"{route.target_url.rstrip('/')}{target_path}"

    # Add query string if present
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    # Prepare headers
    client_ip = request.client.host if request.client else "unknown"
    original_host = request.headers.get("host", "")
    headers = forward_headers(dict(request.headers), client_ip, original_host)

    # Add request ID header
    headers["X-Request-ID"] = request_id

    # Get timeout (route-specific or global)
    timeout = route.timeout or config.timeout

    start_time = time.time()

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=5.0)) as client:
        # Stream the request body
        body = await request.body()

        response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body if body else None,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"Proxied request to {route.name}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": str(request.url.path),
                "target_service": route.name,
                "target_url": target_url,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
            },
        )

        # Build response headers, stripping hop-by-hop
        response_headers = {
            k: v
            for k, v in response.headers.items()
            if k.lower() not in HOP_BY_HOP_HEADERS
        }

        return StreamingResponse(
            content=response.iter_bytes(),
            status_code=response.status_code,
            headers=response_headers,
            media_type=response.headers.get("content-type"),
        )
