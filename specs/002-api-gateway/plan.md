# Implementation Plan: API Gateway Service

**Branch**: `002-api-gateway` | **Date**: 2025-12-26 | **Spec**: [spec.md](spec.md)

## Summary

Add an API Gateway service that acts as the single public entry point for the microservices architecture. The gateway routes incoming HTTP requests to appropriate backend services (service1, service2) based on URL path prefixes, provides health monitoring, and exposes gateway-owned endpoints. It operates as a transparent HTTP proxy without authentication, rate limiting, or payload transformation.

**Technical Approach**: Implement a FastAPI-based HTTP proxy service that uses `httpx` for async request forwarding. Routes are configured via environment variables, and the gateway follows the established monorepo patterns with uv workspace integration.

## Technical Context

**Language/Version**: Python 3.11+ (consistent with existing services)
**Primary Dependencies**: FastAPI 0.100+, httpx 0.25+ (async HTTP client), uvicorn 0.23+
**Storage**: N/A (stateless proxy, no persistence required)
**Testing**: pytest, pytest-asyncio (consistent with existing services)
**Target Platform**: Docker containers (Linux-based), same as existing services
**Project Type**: Microservices monorepo (add new service to existing workspace)
**Performance Goals**: <100ms overhead per request (SC-001, SC-002), 100 concurrent requests (SC-004)
**Constraints**: No auth, no rate limiting, no payload transformation (per Out of Scope)
**Scale/Scope**: 2 backend services initially, configurable for future expansion

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Microservices Architecture ✅ PASS
- Gateway is an independent, deployable service
- Does NOT use Celery task queues (appropriate - synchronous HTTP proxy pattern)
- Communicates via HTTP with backend services (acceptable for edge gateway)
- Will be added as workspace member in monorepo

**Note**: Gateway intentionally uses HTTP instead of Celery because:
1. Synchronous request-response pattern required for external clients
2. Gateway is an edge service, not internal domain service
3. Backend services still communicate via Celery internally

### Principle II: Task Idempotency & Reliability ⚠️ NOT APPLICABLE
- Gateway performs HTTP proxying, not Celery tasks
- Idempotency is handled by backend services
- No task retry logic needed in gateway itself

### Principle III: Monitoring & Observability ✅ PASS
- FR-009: All requests logged with routing decisions
- FR-005: Health check endpoint exposed
- SC-007: Sufficient logging for troubleshooting

### Principle IV: Error Handling & Resilience ✅ PASS
- FR-007: Explicit error responses (404, 502, 503, 504)
- FR-008: Configurable timeout for backend requests
- Edge cases documented with expected behavior

### Principle V: Simplicity First ✅ PASS
- Uses standard FastAPI + httpx (minimal dependencies)
- No auth, rate limiting, circuit breakers (YAGNI - per Out of Scope)
- Configuration via environment variables (12-factor)
- Follows existing service patterns

### Dependency Management ✅ PASS
- Will use uv workspace (FR-012)
- Routes in api.py (FR-013)
- Single .venv at root, standard imports

**Gate Status**: ✅ **PASSED**

## Project Structure

### Documentation (this feature)

```text
specs/002-api-gateway/
├── plan.md              # This file
├── research.md          # Phase 0: HTTP proxy patterns research
├── data-model.md        # Phase 1: Gateway configuration model
├── quickstart.md        # Phase 1: Quick start guide
└── contracts/           # Phase 1: Gateway API contracts
```

### Source Code (repository root)

```text
# Existing monorepo structure (add api-gateway as new workspace member)
.venv/                       # SINGLE virtual environment (root only)
pyproject.toml               # Root: add api-gateway to workspace members
uv.lock                      # Lock file updated after adding gateway

api-gateway/                 # NEW: API Gateway service
├── Dockerfile
├── pyproject.toml           # Package metadata (Python 3.11+, fastapi, httpx)
├── src/
│   └── api_gateway/
│       ├── __init__.py
│       ├── main.py          # FastAPI app initialization
│       ├── api.py           # ALL routes (FR-013)
│       ├── proxy.py         # HTTP forwarding logic
│       ├── config.py        # Route configuration from env vars
│       └── health.py        # Health check endpoint
├── tests/
│   └── test_routing.py
└── .env.example

# Existing services (unchanged)
common/                      # Shared task definitions
worker/                      # Celery worker service
example-service-1/           # Backend service 1
example-service-2/           # Backend service 2
docker-compose.yml           # Updated to include api-gateway
```

**Structure Decision**: Gateway follows the established service pattern (`{service}/src/{package}/`) with routes in `api.py` per FR-013. Added as new workspace member in root `pyproject.toml`.

## Complexity Tracking

No violations - gateway design follows Constitution principles and existing patterns.
