"""
Gateway Configuration Module

Loads configuration from environment variables and provides Pydantic models
for service routes and gateway settings.
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class ServiceRoute(BaseModel):
    """Represents a routing rule mapping URL prefixes to backend services."""

    name: str
    prefix: str = Field(pattern=r"^/.*")
    target_url: str
    strip_prefix: bool = True
    timeout: Optional[int] = Field(None, gt=0)


class GatewayConfig(BaseModel):
    """Global gateway configuration loaded from environment variables."""

    host: str = "0.0.0.0"
    port: int = 8000
    timeout: int = 30
    max_body_size: int = 10 * 1024 * 1024  # 10MB
    log_level: str = "INFO"
    routes: list[ServiceRoute] = []


@lru_cache
def load_config() -> GatewayConfig:
    """
    Load gateway configuration from environment variables.

    Environment variables:
        GATEWAY_HOST: Bind address (default: 0.0.0.0)
        GATEWAY_PORT: Listen port (default: 8000)
        GATEWAY_TIMEOUT: Default request timeout in seconds (default: 30)
        GATEWAY_LOG_LEVEL: Logging level (default: INFO)
        SERVICE1_URL: Backend URL for service1
        SERVICE2_URL: Backend URL for service2

    Returns:
        GatewayConfig: Loaded configuration
    """
    routes = []

    # Load service1 route
    service1_url = os.getenv("SERVICE1_URL")
    if service1_url:
        routes.append(
            ServiceRoute(
                name="service1",
                prefix="/api/service1",
                target_url=service1_url,
                strip_prefix=True,
            )
        )

    # Load service2 route
    service2_url = os.getenv("SERVICE2_URL")
    if service2_url:
        routes.append(
            ServiceRoute(
                name="service2",
                prefix="/api/service2",
                target_url=service2_url,
                strip_prefix=True,
            )
        )

    return GatewayConfig(
        host=os.getenv("GATEWAY_HOST", "0.0.0.0"),
        port=int(os.getenv("GATEWAY_PORT", "8000")),
        timeout=int(os.getenv("GATEWAY_TIMEOUT", "30")),
        log_level=os.getenv("GATEWAY_LOG_LEVEL", "INFO"),
        routes=routes,
    )


def get_route_by_prefix(prefix: str) -> Optional[ServiceRoute]:
    """
    Find a route matching the given prefix.

    Args:
        prefix: URL prefix to match

    Returns:
        ServiceRoute if found, None otherwise
    """
    config = load_config()
    for route in config.routes:
        if prefix.startswith(route.prefix):
            return route
    return None
