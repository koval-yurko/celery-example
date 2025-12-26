"""
Route Matching Module

Handles matching incoming request paths to backend service routes.
"""

from typing import Optional

from api_gateway.config import ServiceRoute, load_config


def match_route(path: str) -> Optional[ServiceRoute]:
    """
    Find a route matching the given path.

    Uses prefix-based matching to find the appropriate backend service.

    Args:
        path: Request path to match

    Returns:
        ServiceRoute if found, None otherwise
    """
    config = load_config()

    for route in config.routes:
        if path.startswith(route.prefix):
            return route

    return None


def rewrite_path(path: str, route: ServiceRoute) -> str:
    """
    Rewrite the request path by stripping the service prefix.

    Example: /api/service1/orders -> /api/orders
    Example: /api/service1 -> /api

    Args:
        path: Original request path
        route: Matched service route

    Returns:
        Rewritten path for backend service
    """
    if route.strip_prefix and path.startswith(route.prefix):
        remaining = path[len(route.prefix) :]
        if remaining:
            return f"/api{remaining}"
        return "/api"
    return path


def is_gateway_owned_path(path: str) -> bool:
    """
    Check if the path is a gateway-owned endpoint.

    Gateway-owned paths are handled directly by the gateway
    without forwarding to backend services.

    Args:
        path: Request path to check

    Returns:
        True if gateway-owned, False otherwise
    """
    gateway_prefixes = ["/health", "/api/gateway"]
    return any(path.startswith(prefix) for prefix in gateway_prefixes)
