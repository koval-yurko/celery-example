# Tasks: API Gateway Service

**Input**: Design documents from `/specs/002-api-gateway/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the specification, so test tasks are not included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This is a **monorepo** with services at root level (per FR-012, Constitution v1.1.0):
- **Root**: `.venv/` (single virtual environment), `pyproject.toml` (workspace config), `uv.lock` (lock file)
- **api-gateway/**: New API Gateway service
- Services follow pattern: `{service-name}/src/{service-name}/`
- **uv** MUST be used for all dependency management
- **ALL routes in api.py** per FR-013

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Create api-gateway service structure and add to monorepo workspace

- [x] T001 Create api-gateway directory structure: Create api-gateway/ with src/api_gateway/ package structure (__init__.py), tests/ directory, and .env.example with GATEWAY_HOST, GATEWAY_PORT, GATEWAY_TIMEOUT, GATEWAY_LOG_LEVEL, SERVICE1_URL, SERVICE2_URL variables
- [x] T002 Create api-gateway/pyproject.toml: Initialize package metadata (name="api-gateway", Python 3.11+), add dependencies (fastapi>=0.100.0, httpx>=0.25.0, uvicorn>=0.23.0, pydantic>=2.0.0), configure hatch build backend with packages=["src/api_gateway"]
- [x] T003 Update root pyproject.toml: Add "api-gateway" to [tool.uv.workspace] members list and [tool.uv.sources] with workspace=true, run `uv sync` to update uv.lock

---

## Phase 2: Foundational (Core Infrastructure)

**Purpose**: Core gateway infrastructure that MUST be complete before user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Implement configuration module in api-gateway/src/api_gateway/config.py: Create GatewayConfig and ServiceRoute Pydantic models (per data-model.md), implement load_config() function reading from environment variables (SERVICE1_URL, SERVICE2_URL, GATEWAY_TIMEOUT etc.), include validation rules for prefixes and URLs
- [x] T005 Implement Pydantic schemas in api-gateway/src/api_gateway/schemas.py: Create GatewayError, HealthStatus, ServiceInfo, and GatewayStatus models (per data-model.md), include error codes enum (not_found, bad_gateway, service_unavailable, gateway_timeout, payload_too_large)
- [x] T006 [P] Implement logging module in api-gateway/src/api_gateway/logging.py: Create structured JSON logging setup with request_id, method, path, target_service, status_code, duration_ms fields (per research.md Decision 8), configure log level from GATEWAY_LOG_LEVEL environment variable
- [x] T007 Create FastAPI app initialization in api-gateway/src/api_gateway/main.py: Initialize FastAPI app with title="API Gateway", version="0.1.0", configure logging on startup, load configuration, include routers from api.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Request Routing to Backend Services (Priority: P1) 🎯 MVP

**Goal**: Enable routing requests from `/api/service1/*` and `/api/service2/*` to corresponding backend services with full request/response preservation

**Independent Test**: Send request to `/api/service1/orders` through gateway, verify it reaches service1's `/api/orders` endpoint with correct payload and returns response

### Implementation for User Story 1

- [x] T008 [US1] Implement proxy module in api-gateway/src/api_gateway/proxy.py: Create async proxy_request() function using httpx.AsyncClient with streaming support (per research.md Decision 3), implement forward_headers() to strip hop-by-hop headers and add X-Forwarded-* headers (per research.md Decision 6), handle connection errors (503) and timeouts (504)
- [x] T009 [US1] Implement route matching in api-gateway/src/api_gateway/routing.py: Create match_route() function for prefix-based routing (per research.md Decision 9), implement rewrite_path() to strip service prefix (e.g., /api/service1/orders → /api/orders), return None for unmatched routes
- [x] T010 [US1] Implement proxy routes in api-gateway/src/api_gateway/api.py: Create FastAPI router, implement catch-all route for /api/service1/{path:path} forwarding to SERVICE1_URL, implement catch-all route for /api/service2/{path:path} forwarding to SERVICE2_URL, preserve all HTTP methods (GET, POST, PUT, DELETE, PATCH)
- [x] T011 [US1] Implement error handling in api-gateway/src/api_gateway/errors.py: Create gateway_error_response() function returning GatewayError JSON (per data-model.md), implement exception handlers for httpx.ConnectError (503), httpx.TimeoutException (504), and general exceptions (502), add error handlers to FastAPI app
- [x] T012 [US1] Add request logging middleware in api-gateway/src/api_gateway/middleware.py: Create RequestLoggingMiddleware that logs request_id, method, path, target_service, status_code, duration_ms for every request (FR-009), generate UUID request_id and add to X-Request-ID header

**Checkpoint**: User Story 1 complete - gateway can route requests to service1 and service2

---

## Phase 4: User Story 2 - Gateway Health Monitoring (Priority: P2)

**Goal**: Enable health checking of the API gateway for container orchestration and monitoring systems

**Independent Test**: Send GET request to `/health`, verify 200 response with health status JSON

### Implementation for User Story 2

- [x] T013 [US2] Implement health endpoint in api-gateway/src/api_gateway/health.py: Create health_check() function returning HealthStatus with status="healthy", service="api-gateway", version from package, timestamp in ISO 8601 format (per research.md Decision 5)
- [x] T014 [US2] Add health route to api-gateway/src/api_gateway/api.py: Add GET /health endpoint that calls health_check(), return 200 with HealthStatus JSON, ensure endpoint responds within 50ms (SC-003)

**Checkpoint**: User Stories 1 and 2 complete - gateway routes requests and provides health monitoring

---

## Phase 5: User Story 3 - Gateway-Owned Endpoints (Priority: P3)

**Goal**: Enable gateway-specific endpoints under `/api/gateway/*` for service discovery and gateway status

**Independent Test**: Send GET request to `/api/gateway/status`, verify response with gateway status and registered services

### Implementation for User Story 3

- [x] T015 [US3] Implement gateway status endpoint in api-gateway/src/api_gateway/gateway.py: Create get_gateway_status() returning GatewayStatus with status="running", version, and list of ServiceInfo for configured routes, create list_services() returning array of ServiceInfo objects
- [x] T016 [US3] Add gateway-owned routes to api-gateway/src/api_gateway/api.py: Add GET /api/gateway/status endpoint returning GatewayStatus JSON, add GET /api/gateway/services endpoint returning array of ServiceInfo, ensure these routes are NOT forwarded to backend services

**Checkpoint**: All user stories complete - gateway provides full routing, health monitoring, and gateway-owned endpoints

---

## Phase 6: Containerization & Integration

**Purpose**: Docker containerization and docker-compose integration

- [x] T017 Create api-gateway/Dockerfile: Use python:3.11-slim base image, copy pyproject.toml and src/, install dependencies with pip, expose port 8000, set CMD to run uvicorn api_gateway.main:app with host 0.0.0.0
- [x] T018 Create api-gateway/.dockerignore: Add .git, __pycache__, *.pyc, .env, .venv, tests/, .pytest_cache, .coverage patterns
- [x] T019 Update docker-compose.yml: Add api-gateway service definition with build context ./api-gateway, expose port 8000, set environment variables (SERVICE1_URL=http://example-service-1:8001, SERVICE2_URL=http://example-service-2:8002), add depends_on for example-service-1 and example-service-2, add to shared network

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation

- [x] T020 Add 404 handling for unknown routes in api-gateway/src/api_gateway/api.py: Implement catch-all route that returns GatewayError with error="not_found" for paths not matching /api/service1/*, /api/service2/*, /api/gateway/*, or /health
- [x] T021 Validate all user stories per quickstart.md: Test routing to service1 and service2, verify health endpoint responds <50ms, verify gateway-owned endpoints work, test error responses (404, 503, 504) by stopping backend services
- [x] T022 Update README.md with gateway documentation: Add API Gateway section describing routing patterns, configuration via environment variables, health check endpoint, gateway-owned endpoints, and example curl commands

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - US1 (Request Routing) can start immediately after Foundational
  - US2 (Health Monitoring) can start in parallel with US1 (different files)
  - US3 (Gateway-Owned Endpoints) can start in parallel with US1/US2 (different files)
- **Containerization (Phase 6)**: Depends on all user stories being complete
- **Polish (Phase 7)**: Depends on Containerization

### User Story Dependencies

```
Phase 2 (Foundational)
    ↓
┌───┴───┐
↓       ↓
Phase 3 (US1: Request Routing) ──┐
Phase 4 (US2: Health Monitoring) ├──► Phase 6 (Containerization)
Phase 5 (US3: Gateway Endpoints)─┘           ↓
                                      Phase 7 (Polish)
```

### Within Each Phase

- **Setup**: Sequential (T001 → T002 → T003)
- **Foundational**: T004 → T005, then T006 and T007 can be parallel
- **US1**: T008 → T009 → T010 → T011 → T012
- **US2**: T013 → T014
- **US3**: T015 → T016
- **Containerization**: T017, T018 can be parallel, then T019

### Parallel Opportunities

- **Phase 2**: T006 (logging) can run parallel to T007 (main.py) after T004, T005
- **Phase 3-5**: All three user story phases can technically run in parallel since they touch different files, but US1 provides the core routing used by validation
- **Phase 6**: T017 (Dockerfile) and T018 (.dockerignore) can run in parallel

---

## Parallel Example: User Story Phases

```bash
# After Foundational phase completes, these can run in parallel:
Task: "Implement proxy module" (US1)
Task: "Implement health endpoint" (US2)
Task: "Implement gateway status endpoint" (US3)

# However, recommended order for incremental validation:
# 1. Complete US1 first (core functionality)
# 2. Then US2 (health checks)
# 3. Then US3 (additional features)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T007) - CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (T008-T012)
4. **STOP and VALIDATE**: Test routing to service1 and service2
5. Demo/review before continuing

**MVP Deliverable**: API Gateway that routes requests to backend services with proper error handling and logging

### Incremental Delivery

1. **Foundation** (Phases 1-2): Setup + config/schemas/logging → Foundation ready (7 tasks)
2. **Iteration 1** (Phase 3): Add US1 → Test independently → Demo (5 tasks, MVP!)
   - Deliverable: Gateway routing requests to service1 and service2
3. **Iteration 2** (Phase 4): Add US2 → Test independently → Demo (2 tasks)
   - Deliverable: Health monitoring for container orchestration
4. **Iteration 3** (Phase 5): Add US3 → Test independently → Demo (2 tasks)
   - Deliverable: Gateway-owned endpoints for service discovery
5. **Containerization** (Phase 6): Add Docker support → Test independently (3 tasks)
   - Deliverable: Containerized gateway in docker-compose
6. **Final Polish** (Phase 7): Cross-cutting concerns → Final validation (3 tasks)

Each story adds value without breaking previous stories.

---

## Task Summary

**Total Tasks**: 22 (T001-T022)
- **Phase 1 (Setup)**: 3 tasks (T001-T003)
- **Phase 2 (Foundational)**: 4 tasks (T004-T007, BLOCKING)
- **Phase 3 (US1 - Request Routing)**: 5 tasks (T008-T012)
- **Phase 4 (US2 - Health Monitoring)**: 2 tasks (T013-T014)
- **Phase 5 (US3 - Gateway-Owned Endpoints)**: 2 tasks (T015-T016)
- **Phase 6 (Containerization)**: 3 tasks (T017-T019)
- **Phase 7 (Polish)**: 3 tasks (T020-T022)

**Parallelization Opportunities**: Limited - most tasks have dependencies, but US phases can overlap

**MVP Scope** (Recommended first delivery):
- Phase 1: Setup (3 tasks)
- Phase 2: Foundational (4 tasks)
- Phase 3: User Story 1 (5 tasks)
- **Total MVP**: 12 tasks

---

## Notes

- **[P] tasks**: Different files, no dependencies - can run in parallel
- **[Story] label**: Maps task to specific user story for traceability and independent testing
- Each user story should be independently completable and testable
- Commit after each task completion
- Stop at any checkpoint to validate story independently
- **FR-013 Compliance**: All routes MUST be defined in api.py (no dynamic route loading)
- **FR-012 Compliance**: Use uv workspace, single .venv at root
