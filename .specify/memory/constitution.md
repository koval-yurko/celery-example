<!--
Sync Impact Report:
- Version: 1.0.1 → 1.1.0 (MINOR - Added uv as dependency management standard)
- Modified Sections:
  - Development Standards: Added new "Dependency Management" subsection
    - uv MUST be used for dependency management and monorepo tooling
    - Single .venv at repository root, no sys.path manipulation
- Principles unchanged: All 5 core principles remain intact
- Template Updates:
  ✅ plan-template.md - No changes needed (constitution check remains valid)
  ✅ spec-template.md - No changes needed (no impact on user stories)
  ✅ tasks-template.md - No changes needed (no impact on task organization)
- Follow-up TODOs: None
-->

# Celery Example Project Constitution

## Core Principles

### I. Microservices Architecture

Services communicate exclusively via Celery task queues. Each microservice MUST:

- Expose functionality as Celery tasks with well-defined contracts
- Maintain independent deployment capability
- Own its data - no direct database sharing between services
- Publish domain events as tasks for cross-service communication
- Define task signatures in a shared contracts module

**Rationale**: Decoupled services enable independent scaling, deployment, and evolution while leveraging Celery's native distributed task execution model.

### II. Task Idempotency & Reliability

All Celery tasks MUST be idempotent and safely retryable. Each task MUST:

- Produce the same result when executed multiple times with identical inputs
- Handle duplicate execution gracefully (e.g., via unique transaction IDs)
- Declare explicit retry policies with backoff strategies
- Use acks_late=True and reject_on_worker_lost=True for critical tasks
- Document side effects and external system interactions

**Rationale**: Distributed systems are inherently unreliable. Idempotent tasks ensure system correctness even under message duplication, network failures, and worker crashes.

### III. Monitoring & Observability

Operational visibility is mandatory. Every service MUST:

- Use structured logging (JSON format) for all task execution
- Emit task lifecycle events (started, succeeded, failed, retried)
- Track task duration, queue depth, and worker utilization metrics
- Include correlation IDs for tracing requests across service boundaries
- Expose health check endpoints and task status queries

**Rationale**: Celery's distributed nature makes debugging and performance optimization impossible without comprehensive observability.

### IV. Error Handling & Resilience

Failures are expected and must be handled explicitly. Each task MUST:

- Define maximum retry attempts and retry intervals
- Implement circuit breaker patterns for external service calls
- Route unrecoverable failures to dead letter queues for analysis
- Distinguish transient errors (retry) from permanent errors (fail fast)
- Never silently swallow exceptions - log and alert on all errors

**Rationale**: Explicit error handling prevents cascade failures, enables root cause analysis, and ensures graceful degradation under partial system failures.

### V. Simplicity First

Complexity must be justified. Development MUST:

- Start with the simplest solution that meets requirements (YAGNI principle)
- Avoid premature optimization and over-abstraction
- Minimize external dependencies - prefer standard library solutions
- Use synchronous tasks by default; introduce async only when needed
- Document any complexity with explicit justification

**Rationale**: Celery adds inherent complexity through distribution. Keeping task logic simple reduces cognitive load, debugging difficulty, and operational overhead.

## Development Standards

### Task Design

- Keep task functions small and focused (single responsibility)
- Pass serializable arguments only (primitives, dicts, lists - no objects)
- Return simple, serializable results
- Tasks can take more than 5 minutes and system should support it
- Use task chains and groups for workflow orchestration

### Testing

- Tests are highly encouraged for all task logic
- Integration tests SHOULD cover task chains and cross-service workflows
- Contract tests SHOULD validate task signatures between services
- Mock external dependencies in unit tests
- Test retry and failure scenarios explicitly

### Service Boundaries

- One microservice per logical domain (e.g., user-service, order-service)
- Services MAY share read-only reference data via events
- Services MUST NOT call each other's databases directly
- Inter-service communication exclusively through Celery tasks
- Define service contracts in `.specify/contracts/` directory

### Dependency Management

This project uses `uv` as the standard tool for dependency management and monorepo coordination. Development MUST:

- Use `uv` for all dependency installation, resolution, and lock file management
- Maintain a single `.venv` virtual environment at the repository root only
- Install all service packages as editable from root: `uv sync` or `pip install -e ./common -e ./worker -e ./service1`
- Use standard Python package imports only - `sys.path.insert()` is FORBIDDEN
- Define shared dependencies in root `pyproject.toml` with workspace configuration
- Generate and commit `uv.lock` for reproducible builds across environments

**Rationale**: `uv` provides fast, reliable dependency resolution with native monorepo support via workspaces. A single virtual environment ensures all services use compatible versions, eliminates path manipulation hacks, and simplifies local development setup.

## Governance

### Constitution Authority

This constitution supersedes all other development practices and coding standards. All code reviews, design decisions, and implementation choices MUST align with these principles.

### Amendment Process

Amendments require:
1. Written proposal documenting the change rationale
2. Analysis of impact on existing services and tasks
3. Approval from project maintainers
4. Migration plan if existing code conflicts with amendment
5. Version bump according to semantic versioning rules

### Compliance Review

- All pull requests MUST verify principle compliance before merge
- Complexity violations (Principle V) MUST include written justification
- Integration tests MUST validate idempotency (Principle II)
- All tasks MUST have documented retry policies (Principle IV)
- Observability requirements (Principle III) are non-negotiable

### Versioning Policy

- **MAJOR**: Backward-incompatible principle changes or removals
- **MINOR**: New principles added or significant guidance expansions
- **PATCH**: Clarifications, wording improvements, or minor corrections

**Version**: 1.1.0 | **Ratified**: 2025-12-25 | **Last Amended**: 2025-12-25