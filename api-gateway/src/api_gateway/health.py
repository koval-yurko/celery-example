"""
Health Check Module

Provides health check functionality for the API gateway.
"""

from datetime import datetime, timezone

from api_gateway import __version__
from api_gateway.schemas import HealthStatus


def health_check() -> HealthStatus:
    """
    Perform a health check of the gateway.

    Returns gateway-only health (does not check backend services)
    per research.md Decision 5.

    Returns:
        HealthStatus with current gateway status
    """
    return HealthStatus(
        status="healthy",
        service="api-gateway",
        version=__version__,
        timestamp=datetime.now(timezone.utc),
    )
