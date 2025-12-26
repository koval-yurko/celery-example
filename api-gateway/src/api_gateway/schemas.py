"""
Gateway Schemas Module

Pydantic models for API responses including errors, health status,
and service information.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ErrorCode(str, Enum):
    """Error codes for gateway-generated errors."""

    NOT_FOUND = "not_found"
    BAD_GATEWAY = "bad_gateway"
    SERVICE_UNAVAILABLE = "service_unavailable"
    GATEWAY_TIMEOUT = "gateway_timeout"
    PAYLOAD_TOO_LARGE = "payload_too_large"


class GatewayError(BaseModel):
    """Standard error response structure for gateway-generated errors."""

    error: str
    message: str
    path: str
    timestamp: datetime
    status_code: int


class HealthStatus(BaseModel):
    """Health check response structure."""

    status: str = "healthy"
    service: str = "api-gateway"
    version: str
    timestamp: datetime


class ServiceInfo(BaseModel):
    """Information about a registered backend service."""

    name: str
    prefix: str
    status: str = "configured"


class GatewayStatus(BaseModel):
    """Gateway status response for gateway-owned endpoints."""

    status: str = "running"
    version: str
    services: list[ServiceInfo] = []
