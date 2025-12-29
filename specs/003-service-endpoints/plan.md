# Implementation Plan: Service Endpoints for Celery Task Examples

**Branch**: `003-service-endpoints` | **Date**: 2025-12-27 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-service-endpoints/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add comprehensive HTTP endpoints to service-1 and service-2 that expose existing Celery task functionality (add, multiply, long_running_task, task_with_progress, process_data) plus new configurable outcome tasks. Implement task history endpoints that query the Celery result backend to demonstrate task lifecycle management, including both successful and failed task scenarios. This demonstrates complete async task patterns including submission, status polling, result retrieval, progress tracking, and failure handling via REST APIs backed by Redis as both message broker and result storage.

## Technical Context

**Language/Version**: Python 3.11+ (matches existing services)
**Primary Dependencies**: FastAPI 0.100+, Celery 5.3+, Redis 7.0+, Pydantic 2.0+, httpx 0.25+
**Storage**: Redis (Celery result backend for task history and results)
**Testing**: pytest 7.4+, pytest-asyncio 0.21+
**Target Platform**: Linux server (Docker containers)
**Project Type**: Microservices (monorepo with uv workspace)
**Performance Goals**:
- Task submission: <100ms (95th percentile)
- Status queries: <50ms (95th percentile)
- Task history retrieval: <1s for 100+ entries
- 100 concurrent requests without errors
**Constraints**:
- HTTP 202/200/400/404/500/503 status codes per REST conventions
- Task results persist indefinitely in Redis backend
- Services remain independently deployable
**Scale/Scope**:
- 6 task types across 2 services
- 10+ new API endpoints (task submission, status, results, history)
- Support 100+ concurrent task submissions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Microservices Architecture ✅ PASS

**Compliance**:
- Service-1 and service-2 already maintain independent deployment capability
- Both services expose Celery tasks with defined contracts (existing common-tasks module)
- Services communicate via Celery task queues (not direct API calls)
- New HTTP endpoints serve as triggers for task submission (fire-and-forget pattern)
- Task history endpoints query shared result backend (read-only, no direct DB sharing)

**Justification**: Feature adds HTTP API layer on top of existing microservices without violating service boundaries. APIs act as task submission interfaces, maintaining Celery-first communication pattern.

### Principle II: Task Idempotency & Reliability ✅ PASS (with action items)

**Compliance**:
- Existing tasks (add, multiply, long_running_task, task_with_progress, process_data) are inherently idempotent
- New configurable outcome task must be designed as idempotent
- Retry policies already configured at Celery worker level

**Action Items for Implementation**:
- Document retry policies in new task implementations
- Ensure configurable outcome task handles duplicate execution gracefully
- Use acks_late=True for new tasks
- Add correlation IDs to task submissions for traceability

### Principle III: Monitoring & Observability ✅ PASS (with enhancements)

**Compliance**:
- Existing services use structured logging
- Health check endpoints already exist
- Task history endpoint provides visibility into task lifecycle

**Enhancements Required**:
- Add correlation ID tracking across API → task → result chain
- Emit task lifecycle events in API endpoints (submission logged, status checked, result retrieved)
- Include request/response logging for new endpoints
- Track metrics: endpoint latency, task submission rate, history query performance

### Principle IV: Error Handling & Resilience ✅ PASS

**Compliance**:
- Spec defines explicit error responses (400, 404, 500, 503)
- Configurable outcome task demonstrates failure scenarios
- Failed tasks queryable via status/result endpoints
- Task history includes both successful and failed tasks

**Implementation Requirements**:
- Implement circuit breaker for Redis connection failures (return 500)
- Return 503 when workers saturated (per timeout-based strategy from clarifications)
- Store error details (message, traceback) in result backend for failed tasks
- Never silently swallow exceptions - log all errors

### Principle V: Simplicity First ✅ PASS

**Compliance**:
- Leverages existing Celery infrastructure (no new queues or workers needed)
- Reuses existing task implementations (5 of 6 tasks already exist)
- No new abstractions or frameworks introduced
- Single new task type (configurable outcome) addresses both success/failure testing

**Justification**: Feature is additive REST API layer over existing async task infrastructure. Complexity limited to FastAPI routing and Celery result backend queries.

### Dependency Management (Constitution v1.1.0) ✅ PASS

**Compliance**:
- Project already uses uv workspace with single .venv at root
- All services installed as editable packages
- No sys.path manipulation required
- Dependencies defined in workspace pyproject.toml

**No Changes Required**: Existing uv workspace structure supports feature implementation.

## Project Structure

### Documentation (this feature)

```text
specs/003-service-endpoints/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── service-1-openapi.yaml
│   └── service-2-openapi.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Microservices monorepo structure (already exists)
example-service-1/
├── src/service1/
│   ├── api.py              # MODIFY: Add new endpoints
│   ├── handlers.py         # MODIFY: Add handler functions
│   └── main.py             # VERIFY: FastAPI app configuration
├── tests/                  # CREATE: Endpoint tests
│   ├── test_api.py
│   └── test_handlers.py
└── pyproject.toml          # VERIFY: Dependencies

example-service-2/
├── src/service2/
│   ├── api.py              # MODIFY: Add new endpoints
│   ├── handlers.py         # MODIFY: Add handler functions
│   └── main.py             # VERIFY: FastAPI app configuration
├── tests/                  # CREATE: Endpoint tests
│   ├── test_api.py
│   └── test_handlers.py
└── pyproject.toml          # VERIFY: Dependencies

common/
├── src/common_tasks/
│   └── tasks.py            # CREATE: New configurable_outcome_task
└── pyproject.toml          # VERIFY: Dependencies

worker/
└── src/worker/
    └── celery_app.py       # VERIFY: Task registration

.venv/                      # Single workspace venv (already exists)
pyproject.toml              # Root workspace config (already exists)
uv.lock                     # Dependency lock file (will update)
```

**Structure Decision**: Existing microservices monorepo structure is preserved. Implementation adds endpoints to existing FastAPI apps in service-1 and service-2, creates one new Celery task in common-tasks, and adds tests. No new services or architectural changes required.

## Complexity Tracking

> **No violations requiring justification**

All constitution principles passed without violations. Implementation follows existing patterns and adds no new complexity beyond standard REST API endpoints backed by Celery task execution.
