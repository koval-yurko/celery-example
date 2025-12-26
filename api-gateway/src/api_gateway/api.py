"""
API Gateway Routes

All routes are defined in this file per FR-013.
"""

import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api_gateway.config import load_config
from api_gateway.errors import create_gateway_error
from api_gateway.gateway import get_gateway_status, list_services
from api_gateway.health import health_check
from api_gateway.proxy import proxy_request, rewrite_path
from api_gateway.routing import match_route
from api_gateway.schemas import ErrorCode, GatewayStatus, HealthStatus, ServiceInfo

router = APIRouter()


# Health check endpoint (US2)
@router.get("/health", response_model=HealthStatus)
async def get_health():
    """
    Get gateway health status.

    Returns gateway-only health (does not check backend services).
    Should respond within 50ms per SC-003.
    """
    return health_check()


# Gateway-owned endpoints (US3)
@router.get("/api/gateway/status", response_model=GatewayStatus)
async def gateway_status():
    """
    Get gateway status including registered services.

    Returns gateway status and list of configured backend services.
    """
    return get_gateway_status()


@router.get("/api/gateway/services", response_model=list[ServiceInfo])
async def gateway_services():
    """
    Get list of registered backend services.

    Returns array of ServiceInfo objects for each configured route.
    """
    return list_services()


# Proxy routes for service1
@router.api_route(
    "/api/service1/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
)
async def proxy_service1(request: Request, path: str):
    """Proxy all requests to service1."""
    return await _handle_proxy_request(request, f"/api/service1/{path}")


@router.api_route(
    "/api/service1",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
)
async def proxy_service1_root(request: Request):
    """Proxy root requests to service1."""
    return await _handle_proxy_request(request, "/api/service1")


# Proxy routes for service2
@router.api_route(
    "/api/service2/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
)
async def proxy_service2(request: Request, path: str):
    """Proxy all requests to service2."""
    return await _handle_proxy_request(request, f"/api/service2/{path}")


@router.api_route(
    "/api/service2",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
)
async def proxy_service2_root(request: Request):
    """Proxy root requests to service2."""
    return await _handle_proxy_request(request, "/api/service2")


async def _handle_proxy_request(request: Request, original_path: str):
    """
    Handle proxy request routing and forwarding.

    Args:
        request: Incoming FastAPI request
        original_path: Original request path

    Returns:
        Proxied response or error response
    """
    import httpx

    request_id = str(uuid.uuid4())

    # Match route
    route = match_route(original_path)

    if not route:
        return create_gateway_error(
            error_code=ErrorCode.NOT_FOUND,
            message=f"No route found for path: {original_path}",
            path=original_path,
            status_code=404,
        )

    # Rewrite path
    target_path = rewrite_path(original_path, route)

    try:
        return await proxy_request(request, route, target_path, request_id)
    except httpx.ConnectError:
        return create_gateway_error(
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            message=f"Backend service '{route.name}' is not responding",
            path=original_path,
            status_code=503,
        )
    except httpx.TimeoutException:
        config = load_config()
        timeout = route.timeout or config.timeout
        return create_gateway_error(
            error_code=ErrorCode.GATEWAY_TIMEOUT,
            message=f"Request to '{route.name}' timed out after {timeout} seconds",
            path=original_path,
            status_code=504,
        )
    except Exception as e:
        return create_gateway_error(
            error_code=ErrorCode.BAD_GATEWAY,
            message=f"Error forwarding request to '{route.name}': {str(e)}",
            path=original_path,
            status_code=502,
        )


# Catch-all 404 for unknown routes
@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
)
async def catch_all_not_found(request: Request, path: str):
    """
    Catch-all route for unmatched paths.

    Returns 404 for any path not matching:
    - /health
    - /api/gateway/*
    - /api/service1/*
    - /api/service2/*
    """
    return create_gateway_error(
        error_code=ErrorCode.NOT_FOUND,
        message=f"No route found for path: /{path}",
        path=f"/{path}",
        status_code=404,
    )
