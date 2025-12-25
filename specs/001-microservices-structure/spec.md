# Feature Specification: Microservices Repository Structure

**Feature Branch**: `001-microservices-structure`
**Created**: 2025-12-25
**Status**: Draft
**Input**: User description: "Update repository structure to support microservices approach - have separate folder for each service with Dockerfile instructions how to build and run it in isolation. Have separate folder for common/tasks functionality which can be used by any other service. But also create worker service (with own Dockerfile and dependencies) which will handle tasks execution"

## Architectural Constraints

### Monorepo Structure

This project follows a **monorepo architecture** with the following constraints:

1. **Single Virtual Environment**: A single `.venv` directory MUST exist at the repository root level only. Individual services MUST NOT have their own virtual environments.

2. **Centralized Dependency Management**: All dependencies MUST be managed at the root level. Services share the common environment but declare their specific dependencies in their build configurations for containerization.

3. **Explicit Path Resolution**: Services MUST NOT use dynamic path manipulation such as `sys.path.insert()` or similar runtime path modifications. All imports MUST use explicit, package-relative paths that are resolvable through standard module resolution.

4. **API Route Organization**: API route definitions MUST remain within the `api.py` file of each service. Routes MUST NOT be split across multiple files or dynamically loaded from external locations.

### Dependency Management Rules

- **Tool**: `uv` MUST be used as the dependency management and monorepo coordination tool (per Constitution v1.1.0)
- **Root Level**: The root `pyproject.toml` defines all shared dependencies, development tooling, and workspace configuration
- **Lock File**: `uv.lock` MUST be generated and committed for reproducible builds across all environments
- **Service Level**: Each service's containerization instructions (Dockerfile) define production dependencies needed for that service
- **Common Module**: The common module is treated as an internal package, installed via local path reference in both development (root venv) and production (container build) contexts
- **Version Consistency**: All services running in the same environment MUST use compatible dependency versions resolved from the root configuration via `uv.lock`

## Clarifications

### Session 2025-12-25

- Q: Common Module Versioning Strategy - How are version conflicts handled when different services need different versions? → A: All services MUST use the same common module version at all times (breaking changes require updating all services before deployment)
- Q: Worker Crash Recovery Behavior - What happens to tasks when a worker crashes during execution? → A: Tasks MUST be automatically re-queued and retried on a different worker when the original worker crashes (using acks_late=True and task retry policies)
- Q: Service Configuration Management - How do services receive environment-specific configuration (broker URLs, secrets) across different environments? → A: Configuration injected via environment variables at runtime; containers read from environment on startup (12-factor app pattern)
- Q: Cross-Network Service Communication - How do services communicate when deployed in different networks or environments? → A: All services connect to the same shared Redis broker regardless of network location; broker handles cross-network routing
- Q: New Service Integration Process - How do new services integrate with the existing common module? → A: New services declare the common module as a standard dependency in their build configuration; module installed automatically during container build

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Service Isolation (Priority: P1)

As a developer, I need to run and test individual services in complete isolation so that I can work on one service without requiring all other services to be running, reducing local development complexity and resource usage.

**Why this priority**: This is the foundation of microservices architecture - without service isolation, we can't achieve independent development, testing, or deployment.

**Independent Test**: Can be fully tested by starting a single service in isolation, sending it requests, and verifying it responds correctly without any other services running.

**Acceptance Scenarios**:

1. **Given** a service folder with its own dependencies, **When** a developer builds and runs only that service, **Then** the service starts successfully and can handle requests independently
2. **Given** multiple services in the repository, **When** a developer modifies one service, **Then** other services are not affected and don't require rebuilds
3. **Given** a service running in isolation, **When** the service needs to communicate with another service, **Then** it can do so via task queues without direct dependencies

---

### User Story 2 - Shared Task Definitions (Priority: P2)

As a developer, I need to access common task definitions and shared utilities across all services so that services can communicate through standardized task contracts without duplicating code.

**Why this priority**: After establishing service isolation (P1), we need a way for services to share task contracts and common utilities while maintaining loose coupling.

**Independent Test**: Can be fully tested by importing the common module from two different services, verifying both can call shared task definitions, and confirming changes to common code are immediately available to all services.

**Acceptance Scenarios**:

1. **Given** a common tasks module, **When** any service imports it, **Then** the service can access all shared task definitions and utilities
2. **Given** a task defined in the common module, **When** one service publishes the task, **Then** any worker can execute it using the shared definition
3. **Given** an update to the common module, **When** services are rebuilt, **Then** all services use the updated version without code duplication

---

### User Story 3 - Dedicated Task Workers (Priority: P3)

As a system operator, I need dedicated worker services that exclusively execute tasks so that I can scale task processing independently from business services and isolate resource-intensive task execution.

**Why this priority**: After services can share task definitions (P2), we need dedicated workers that can be scaled independently based on task queue depth.

**Independent Test**: Can be fully tested by deploying only worker services (no business services), publishing tasks to the queue externally, and verifying workers consume and execute tasks successfully.

**Acceptance Scenarios**:

1. **Given** a worker service running independently, **When** tasks are published to the queue, **Then** the worker consumes and executes them without requiring business services
2. **Given** high task queue depth, **When** additional worker instances are started, **Then** task processing throughput increases linearly
3. **Given** a worker service with specific resource requirements, **When** the worker is deployed, **Then** it runs with its own isolated dependencies and configuration

---

### User Story 4 - Containerized Deployment (Priority: P4)

As a developer or operator, I need to build and run each service using standardized container instructions so that environments are consistent across development, testing, and production.

**Why this priority**: After all service types are defined (P1-P3), we need a standardized way to build, run, and deploy them consistently.

**Independent Test**: Can be fully tested by building a service container from scratch on a clean machine, running it, and verifying it operates identically to development environments.

**Acceptance Scenarios**:

1. **Given** a service folder with container instructions, **When** a developer builds the container, **Then** the build completes successfully with all dependencies included
2. **Given** a built container, **When** the container is run in any environment, **Then** the service behaves identically regardless of host system differences
3. **Given** container instructions for a service, **When** a new developer follows them, **Then** they can run the service locally without manual dependency installation

---

### Edge Cases

- No remaining unresolved edge cases (all addressed in clarifications)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Repository MUST provide isolated directory structure where each service has its own self-contained folder
- **FR-002**: Each service folder MUST include containerization instructions defining build and runtime requirements
- **FR-003**: Repository MUST provide a common module for shared task definitions and utilities accessible to all services; all services MUST use the same version of the common module at any given time
- **FR-004**: Repository MUST include a dedicated worker service that executes tasks without containing business logic
- **FR-005**: Each service MUST be buildable and runnable in complete isolation without requiring other services to be present
- **FR-006**: Services MUST communicate exclusively through task queues using shared task definitions from the common module
- **FR-007**: Worker service MUST have its own isolated dependencies and configuration independent of business services
- **FR-008**: Each service's containerization instructions MUST specify exact dependency versions for reproducible builds
- **FR-009**: Repository structure MUST support adding new services without modifying existing service code
- **FR-010**: Common module MUST be importable by all services and workers without circular dependencies
- **FR-011**: Worker services MUST implement automatic task re-queuing on worker crashes using late acknowledgment and retry policies to prevent task loss
- **FR-012**: All services MUST accept configuration through environment variables at runtime (broker URLs, secrets, environment-specific settings) following 12-factor app methodology; no configuration baked into container images
- **FR-013**: New services MUST declare the common module as a build-time dependency in their containerization instructions; the module is installed automatically during the container build process
- **FR-014**: Repository MUST use a single virtual environment (`.venv`) located at the repository root; individual services MUST NOT maintain separate virtual environments
- **FR-015**: All dependencies MUST be managed centrally at the root level with a single dependency configuration file (e.g., `pyproject.toml`)
- **FR-016**: Services MUST NOT use dynamic path manipulation (such as `sys.path.insert()`) for module resolution; all imports MUST use explicit package-relative paths resolvable through standard module resolution
- **FR-017**: API routes for each service MUST be defined within that service's `api.py` file; routes MUST NOT be dynamically loaded from external locations or split across multiple files
- **FR-018**: Repository MUST use `uv` as the dependency management tool for installation, resolution, and lock file management (per Constitution v1.1.0 Dependency Management standard)
- **FR-019**: Repository MUST include a `uv.lock` file at the root level for reproducible dependency resolution across all environments

### Key Entities

- **Service**: An independent unit of business functionality with its own directory, dependencies, containerization instructions, and lifecycle (examples: user-service, order-service, notification-service)
- **Common Module**: A shared library containing task definitions, shared utilities, and contracts used across all services
- **Worker Service**: A specialized service dedicated to consuming and executing tasks from queues without exposing business APIs
- **Container Instructions**: Specifications defining how to build, configure, and run each service in an isolated container environment

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Any service can be built and started in under 3 minutes on a clean environment using only its container instructions
- **SC-002**: Developers can run a single service in isolation using less than 50% of the resources required to run the entire application
- **SC-003**: Worker services can be scaled from 1 to 10 instances without requiring changes to business service code or configuration
- **SC-004**: Adding a new service to the repository requires zero modifications to existing service code (only additions)
- **SC-005**: Services built from container instructions on different machines (Linux, macOS, Windows with containers) behave identically in 100% of test scenarios
- **SC-006**: Task execution throughput can be increased by 200% by scaling only worker services without scaling business services
- **SC-007**: Common module updates can be deployed to all services by rebuilding containers in under 10 minutes total
- **SC-008**: Developers can verify service isolation by running integration tests against one service while all others are stopped
- **SC-009**: All service imports resolve correctly using standard module resolution without any runtime path manipulation
- **SC-010**: A single `uv sync` command from the repository root installs all dependencies for local development of all services
- **SC-011**: Dependency resolution via `uv.lock` produces identical environments on any developer machine or CI system

## Assumptions

- **Assumption 1**: All services will use the same centralized message broker (Redis) for task queue communication regardless of network location; the broker is network-accessible to all services and handles cross-network routing
- **Assumption 2**: Services will use container technology (Docker) as the standardization mechanism for build and deployment
- **Assumption 3**: The common module will be versioned; all services MUST use the same common module version simultaneously (breaking changes require coordinated updates across all services before deployment)
- **Assumption 4**: Each service will maintain its own data store and will not share databases directly with other services (per Constitution Principle I)
- **Assumption 5**: Worker services will use the same task framework (Celery) as the current implementation
- **Assumption 6**: Development, testing, and production environments all support container orchestration
- **Assumption 7**: Environment variables are the standard mechanism for runtime configuration injection across all deployment environments
- **Assumption 8**: This is a proof-of-concept (POC) implementation focused on exploring Celery in a microservices architecture; simplicity is prioritized over production-grade features, with improvements planned for future iterations

## POC Exemptions from Constitution

This POC implementation defers certain production-grade constitution requirements to future iterations. The following principles are **partially implemented** with simplified approaches:

### Deferred: Constitution Principle II (Task Idempotency & Reliability)
- **Deferred**: Explicit idempotency checks with unique transaction IDs
- **Deferred**: Comprehensive retry policies with exponential backoff
- **POC Approach**: Basic Celery retry configuration without production-grade idempotency guarantees
- **Migration Path**: Add idempotency middleware and transaction ID tracking in post-POC iteration

### Deferred: Constitution Principle III (Monitoring & Observability)
- **Deferred**: Structured JSON logging
- **Deferred**: Task lifecycle event emission
- **Deferred**: Metrics collection (task duration, queue depth, worker utilization)
- **Deferred**: Correlation ID propagation across services
- **POC Approach**: Basic print/log statements for debugging
- **Migration Path**: Integrate structured logging library (e.g., structlog) and metrics backend (e.g., Prometheus) in post-POC iteration

### Deferred: Constitution Principle IV (Error Handling & Resilience)
- **Deferred**: Circuit breaker patterns for external service calls
- **Deferred**: Dead letter queue routing for unrecoverable failures
- **Deferred**: Sophisticated transient vs permanent error distinction
- **POC Approach**: Basic exception handling with simple retry logic
- **Migration Path**: Add circuit breaker library (e.g., pybreaker) and DLQ configuration in post-POC iteration

### Maintained: Constitution Principles I & V
- ✅ **Principle I (Microservices Architecture)**: Fully implemented via task queue communication
- ✅ **Principle V (Simplicity First)**: Core principle guiding POC design

**Rationale**: This POC prioritizes demonstrating core Celery microservices patterns (service isolation, shared task definitions, dedicated workers, containerization) over production-grade operational features. The deferred features represent approximately 40-50% additional implementation effort and are not required to validate the architectural approach.

## Out of Scope

- Migration of existing code to new services (this spec covers structure only, not service implementation)
- Service discovery and load balancing mechanisms between services
- Monitoring and observability infrastructure for distributed services (POC will use basic logging)
- CI/CD pipeline configuration for building and deploying services
- Inter-service authentication and authorization mechanisms
- Service mesh or advanced networking configurations
- Database migration strategies for services with persistent state
- Production-grade features such as advanced monitoring, circuit breakers, or comprehensive error handling (POC focuses on demonstrating core Celery microservices patterns)