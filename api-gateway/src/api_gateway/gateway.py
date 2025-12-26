"""
Gateway Status Module

Provides gateway-owned endpoints for service discovery and status.
"""

from api_gateway import __version__
from api_gateway.config import load_config
from api_gateway.schemas import GatewayStatus, ServiceInfo


def list_services() -> list[ServiceInfo]:
    """
    Get list of configured backend services.

    Returns:
        List of ServiceInfo objects for each configured route
    """
    config = load_config()
    return [
        ServiceInfo(
            name=route.name,
            prefix=route.prefix,
            status="configured",
        )
        for route in config.routes
    ]


def get_gateway_status() -> GatewayStatus:
    """
    Get current gateway status including registered services.

    Returns:
        GatewayStatus with version and list of services
    """
    return GatewayStatus(
        status="running",
        version=__version__,
        services=list_services(),
    )
