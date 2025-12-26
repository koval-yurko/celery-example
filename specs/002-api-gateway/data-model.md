# Data Model: API Gateway Service

**Feature**: 002-api-gateway
**Date**: 2025-12-26

## Overview

The API Gateway is a stateless service - it does not persist any data. This document describes the runtime data structures used for configuration, request handling, and response generation.

---

## Entities

### 1. ServiceRoute

Represents a routing rule mapping incoming URL prefixes to backend services.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Service identifier (e.g., "service1", "service2") |
| `prefix` | string | Yes | URL prefix to match (e.g., "/api/service1") |
| `target_url` | string | Yes | Backend service base URL (e.g., "http://example-service-1:8001") |
| `strip_prefix` | boolean | Yes | Whether to remove prefix when forwarding (default: true) |
| `timeout` | integer | No | Request timeout in seconds (overrides global, optional) |

**Validation Rules**:
- `prefix` must start with "/"
- `prefix` must not end with "/" (normalized)
- `target_url` must be a valid HTTP/HTTPS URL
- `timeout` must be > 0 if specified

**Example**:
```python
ServiceRoute(
    name="service1",
    prefix="/api/service1",
    target_url="http://example-service-1:8001",
    strip_prefix=True,
    timeout=None  # Use global timeout
)
```

---

### 2. GatewayConfig

Global gateway configuration loaded from environment variables.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `host` | string | No | "0.0.0.0" | Bind address |
| `port` | integer | No | 8000 | Listen port |
| `timeout` | integer | No | 30 | Default request timeout (seconds) |
| `max_body_size` | integer | No | 10MB | Maximum request body size (bytes) |
| `log_level` | string | No | "INFO" | Logging level |
| `routes` | list[ServiceRoute] | Yes | - | Configured service routes |

**Environment Variable Mapping**:
```
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8000
GATEWAY_TIMEOUT=30
GATEWAY_MAX_BODY_SIZE=10485760
GATEWAY_LOG_LEVEL=INFO
SERVICE1_URL=http://example-service-1:8001
SERVICE2_URL=http://example-service-2:8002
```

---

### 3. ProxyRequest

Represents an incoming request being processed by the gateway.

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | string (UUID) | Unique identifier for tracing |
| `method` | string | HTTP method (GET, POST, etc.) |
| `path` | string | Original request path |
| `headers` | dict | Original request headers |
| `query_params` | dict | URL query parameters |
| `body` | bytes/stream | Request body (if any) |
| `client_ip` | string | Client IP address |
| `timestamp` | datetime | Request received time |

**Derived Fields** (computed during routing):
- `matched_route`: ServiceRoute or None
- `target_path`: Rewritten path after prefix stripping
- `target_url`: Full URL to forward to

---

### 4. ProxyResponse

Represents the response returned to the client.

| Field | Type | Description |
|-------|------|-------------|
| `status_code` | integer | HTTP status code |
| `headers` | dict | Response headers |
| `body` | bytes/stream | Response body |
| `duration_ms` | integer | Total processing time |
| `source` | string | "backend" or "gateway" |

---

### 5. GatewayError

Standard error response structure for gateway-generated errors.

| Field | Type | Description |
|-------|------|-------------|
| `error` | string | Error code (e.g., "not_found", "service_unavailable") |
| `message` | string | Human-readable error message |
| `path` | string | Original request path |
| `timestamp` | string | ISO 8601 timestamp |
| `status_code` | integer | HTTP status code |

**Error Codes**:
| Code | Status | Description |
|------|--------|-------------|
| `not_found` | 404 | No route matches the request path |
| `bad_gateway` | 502 | Backend service returned invalid response |
| `service_unavailable` | 503 | Backend service is not reachable |
| `gateway_timeout` | 504 | Backend service did not respond in time |
| `payload_too_large` | 413 | Request body exceeds max size |

---

### 6. HealthStatus

Health check response structure.

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | "healthy" or "unhealthy" |
| `service` | string | "api-gateway" |
| `version` | string | Gateway version (e.g., "0.1.0") |
| `timestamp` | string | ISO 8601 timestamp |

---

### 7. ServiceInfo

Information about a registered backend service (for gateway-owned endpoints).

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Service identifier |
| `prefix` | string | URL prefix handled by this service |
| `status` | string | "configured" (not health-checked) |

---

## Relationships

```
GatewayConfig
    │
    └── routes: list[ServiceRoute]
                    │
                    └── Used by ProxyRequest to determine routing
                            │
                            └── Generates ProxyResponse or GatewayError
```

---

## State Transitions

The gateway is stateless - no persistent state transitions. However, request processing follows this flow:

```
[Incoming Request]
       │
       ▼
[Parse ProxyRequest]
       │
       ▼
[Match ServiceRoute] ──── No Match ──► [Return 404 GatewayError]
       │
       │ Match Found
       ▼
[Rewrite Path]
       │
       ▼
[Forward to Backend] ──── Timeout ──► [Return 504 GatewayError]
       │                    │
       │                    └── Connection Error ──► [Return 503 GatewayError]
       │
       ▼
[Return ProxyResponse]
```

---

## Pydantic Models (Implementation Reference)

```python
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class ServiceRoute(BaseModel):
    name: str
    prefix: str = Field(pattern=r"^/.*")
    target_url: HttpUrl
    strip_prefix: bool = True
    timeout: Optional[int] = Field(None, gt=0)

class GatewayConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    timeout: int = 30
    max_body_size: int = 10 * 1024 * 1024  # 10MB
    log_level: str = "INFO"
    routes: list[ServiceRoute]

class GatewayError(BaseModel):
    error: str
    message: str
    path: str
    timestamp: datetime
    status_code: int

class HealthStatus(BaseModel):
    status: str = "healthy"
    service: str = "api-gateway"
    version: str
    timestamp: datetime

class ServiceInfo(BaseModel):
    name: str
    prefix: str
    status: str = "configured"
```
