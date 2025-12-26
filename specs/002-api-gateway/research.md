# Research: API Gateway Service

**Feature**: 002-api-gateway
**Date**: 2025-12-26

## Research Topics

This document captures technical decisions and research findings for the API Gateway implementation.

---

## Decision 1: HTTP Client Library

**Question**: Which HTTP client library to use for proxying requests to backend services?

**Decision**: `httpx`

**Rationale**:
- Native async/await support (matches FastAPI's async model)
- Streaming support for large request/response bodies
- Connection pooling built-in for performance
- Modern API, actively maintained
- Already used in similar FastAPI proxy patterns

**Alternatives Considered**:
- `aiohttp`: Heavier, more complex API, less intuitive for simple proxying
- `requests`: Synchronous only, would block the event loop
- `urllib3`: Lower-level, requires more boilerplate

---

## Decision 2: Routing Configuration Pattern

**Question**: How to configure service routes (URL patterns → backend URLs)?

**Decision**: Environment variables with structured naming convention

**Rationale**:
- Follows 12-factor app methodology (per FR-011)
- Consistent with existing services in the monorepo
- Easy to override in docker-compose.yml
- No code changes needed to add new routes (per SC-005)

**Configuration Pattern**:
```
SERVICE1_URL=http://example-service-1:8001
SERVICE2_URL=http://example-service-2:8002
GATEWAY_TIMEOUT=30
GATEWAY_MAX_BODY_SIZE=10485760
```

**Alternatives Considered**:
- YAML/JSON config file: Requires volume mounting, more complex deployment
- Database-backed config: Overkill for static routing, adds dependency
- Code-based routing: Violates SC-005 (config-only changes)

---

## Decision 3: Request Forwarding Strategy

**Question**: How to handle request forwarding (streaming vs buffered)?

**Decision**: Streaming proxy for both requests and responses

**Rationale**:
- Supports large payloads without memory bloat
- Lower latency (no full buffering before forwarding)
- Required for future WebSocket support (if added later)
- Standard practice for API gateways

**Implementation Approach**:
```python
async def proxy_request(request: Request, target_url: str) -> StreamingResponse:
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=forward_headers(request.headers),
            content=request.stream(),
            timeout=settings.timeout,
        )
        return StreamingResponse(
            content=response.aiter_bytes(),
            status_code=response.status_code,
            headers=dict(response.headers),
        )
```

**Alternatives Considered**:
- Buffered proxy: Simpler but memory-intensive for large payloads
- Request body size limit only: Still requires buffering, not ideal

---

## Decision 4: Error Response Format

**Question**: How should gateway errors be formatted?

**Decision**: JSON error responses with consistent structure

**Rationale**:
- Consistent with FastAPI's default error format
- Machine-parseable for client error handling
- Includes useful debugging info (error type, path, timestamp)
- Matches backend services' error format

**Error Response Schema**:
```json
{
  "error": "service_unavailable",
  "message": "Backend service 'service1' is not responding",
  "path": "/api/service1/orders",
  "timestamp": "2025-12-26T12:00:00Z",
  "status_code": 503
}
```

**Alternatives Considered**:
- Plain text errors: Less structured, harder to parse
- Backend-passthrough only: Doesn't cover gateway-specific errors (502, 504)

---

## Decision 5: Health Check Design

**Question**: What should the health check endpoint return?

**Decision**: Gateway-only health (does not check backend services)

**Rationale**:
- Per User Story 2, Scenario 2: "backend availability is not part of gateway health"
- Faster health checks (no network calls to backends)
- Container orchestration only needs to know if gateway process is running
- Backend health is monitored separately

**Health Response Schema**:
```json
{
  "status": "healthy",
  "service": "api-gateway",
  "version": "0.1.0",
  "timestamp": "2025-12-26T12:00:00Z"
}
```

**Alternatives Considered**:
- Deep health check (ping backends): Slower, conflates gateway and service health
- Liveness vs readiness separation: Overkill for POC, can add later

---

## Decision 6: Header Forwarding Policy

**Question**: Which headers to forward/strip when proxying?

**Decision**: Forward all headers except hop-by-hop headers

**Rationale**:
- Preserves authentication tokens (Authorization header)
- Preserves content negotiation headers (Accept, Content-Type)
- Hop-by-hop headers (Connection, Keep-Alive, etc.) are HTTP/1.1 specific
- Standard proxy behavior per RFC 7230

**Headers to Strip**:
- `Connection`
- `Keep-Alive`
- `Transfer-Encoding`
- `TE`
- `Trailer`
- `Upgrade`

**Headers to Add**:
- `X-Forwarded-For`: Client IP
- `X-Forwarded-Proto`: Original protocol (http/https)
- `X-Forwarded-Host`: Original host header

**Alternatives Considered**:
- Allowlist only: Too restrictive, breaks unknown headers
- Forward everything: Breaks HTTP protocol semantics

---

## Decision 7: Timeout Strategy

**Question**: How to handle request timeouts to backend services?

**Decision**: Single configurable timeout per request (default 30s)

**Rationale**:
- Simple and predictable behavior
- Covers both connection and read timeouts
- 30s default is reasonable for most API operations
- Environment variable override for different deployments

**Implementation**:
```python
GATEWAY_TIMEOUT = int(os.getenv("GATEWAY_TIMEOUT", "30"))

# In httpx client
timeout = httpx.Timeout(GATEWAY_TIMEOUT, connect=5.0)
```

**Alternatives Considered**:
- Per-route timeouts: More complex config, not needed for POC
- Separate connect/read timeouts: Over-engineering for initial implementation
- No timeout: Dangerous, could hang indefinitely

---

## Decision 8: Logging Strategy

**Question**: How to log requests for FR-009 compliance?

**Decision**: Structured logging with request ID correlation

**Rationale**:
- JSON format for log aggregation systems
- Request ID enables tracing across gateway → backend
- Includes timing information for performance analysis
- Follows Constitution Principle III (Monitoring & Observability)

**Log Fields**:
```json
{
  "timestamp": "2025-12-26T12:00:00Z",
  "request_id": "uuid",
  "method": "POST",
  "path": "/api/service1/orders",
  "target_service": "service1",
  "target_url": "http://example-service-1:8001/api/orders",
  "status_code": 200,
  "duration_ms": 45,
  "client_ip": "192.168.1.1"
}
```

**Alternatives Considered**:
- Plain text logs: Harder to parse and aggregate
- Minimal logging: Insufficient for troubleshooting (violates SC-007)

---

## Decision 9: Route Matching Pattern

**Question**: How to match incoming paths to backend services?

**Decision**: Prefix-based routing with path rewriting

**Rationale**:
- Simple and predictable (per Principle V)
- Matches spec requirements (FR-001, FR-002)
- Easy to extend for new services

**Routing Table**:
| Incoming Path | Target Service | Rewritten Path |
|---------------|----------------|----------------|
| `/api/service1/*` | service1 | `/api/*` |
| `/api/service2/*` | service2 | `/api/*` |
| `/api/gateway/*` | (local) | (no rewrite) |
| `/health` | (local) | (no rewrite) |

**Implementation**:
```python
ROUTES = {
    "service1": {"prefix": "/api/service1", "target": os.getenv("SERVICE1_URL")},
    "service2": {"prefix": "/api/service2", "target": os.getenv("SERVICE2_URL")},
}
```

**Alternatives Considered**:
- Regex-based routing: Over-complex for current needs
- Path-to-path mapping: Less flexible, more config overhead

---

## Summary

All technical decisions align with:
- **Constitution Principle V** (Simplicity First): Minimal dependencies, straightforward patterns
- **FR-012**: Monorepo structure with uv workspace
- **FR-013**: Routes in api.py
- **SC-005**: Configuration-only changes for new routes

No NEEDS CLARIFICATION items remain - all technical decisions resolved.
