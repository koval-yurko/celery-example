# Research: Microservices Repository Structure

**Feature**: 001-microservices-structure
**Date**: 2025-12-25
**Status**: Complete

## Overview

This document captures architectural decisions and technology choices for implementing a Celery-based microservices repository structure as a proof-of-concept.

---

## Decision 1: Task Queue Framework

**Decision**: Use Celery 5.3+ with Redis as broker and result backend

**Rationale**:
- Celery is the de facto standard for distributed task queues in Python
- Mature ecosystem with strong community support
- Native support for multiple brokers (Redis chosen for simplicity)
- Built-in features: retries, task routing, result persistence, worker pools
- Well-documented patterns for microservices communication

**Alternatives Considered**:
- **RabbitMQ + Celery**: More robust broker but adds operational complexity for POC
- **Apache Kafka**: Overkill for simple task queues; designed for event streaming at scale
- **RQ (Redis Queue)**: Simpler but lacks features needed for production (no retry policies, limited task routing)
- **Custom solution with Redis pub/sub**: Reinventing the wheel; would need to implement retry logic, result tracking, etc.

**References**:
- Celery documentation: https://docs.celeryq.dev/en/stable/
- Redis as Celery broker: https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html

---

## Decision 2: Service Isolation Strategy

**Decision**: Each service as separate root-level directory with own Dockerfile and dependencies

**Rationale**:
- Clear boundaries between services (no accidental cross-dependencies)
- Independent deployment capability (each service builds separately)
- Enables different dependency versions per service if needed (though POC uses same versions)
- Aligns with microservices principle: independently deployable units
- Easier to extract services into separate repositories later if needed

**Alternatives Considered**:
- **Monorepo with services/ folder**: Adds unnecessary nesting; services at root is cleaner
- **Separate git repositories**: Too much overhead for POC; complicates common module sharing
- **Single codebase with modules**: Defeats purpose of service isolation; can't deploy independently

**References**:
- Microservices patterns: https://microservices.io/patterns/microservices.html
- Conway's Law considerations: Team structure should match service boundaries

---

## Decision 3: Common Module Packaging

**Decision**: Shared `common_tasks` module installed as dependency in all services

**Rationale**:
- Single source of truth for task contracts (no drift between services)
- Type safety via Pydantic schemas shared across services
- Celery app configuration centralized (broker URLs, serialization, etc.)
- Standard Python packaging (pyproject.toml) enables installation in containers
- Version pinning ensures all services use same contracts

**Alternatives Considered**:
- **Duplicate task definitions**: Would cause contract drift, maintenance nightmare
- **Code generation from schemas**: Over-engineering for POC; adds build complexity
- **gRPC/Protobuf contracts**: Wrong abstraction layer; Celery tasks use Python directly
- **Shared volume in Docker**: Anti-pattern; breaks container immutability

**Trade-offs**:
- **Pro**: Consistency, type safety, single update point
- **Con**: All services must use same common module version (coordinated updates)
- **Mitigation**: Version common module carefully; breaking changes require updating all services

---

## Decision 4: Worker Architecture

**Decision**: Dedicated worker service separate from business services

**Rationale**:
- Enables independent scaling of task execution vs. request handling
- Workers can have different resource profiles (CPU, memory) than API services
- Failure isolation: Worker crashes don't affect API availability
- Deployment flexibility: Can deploy workers in different regions/networks
- Aligns with Constitution Principle I (microservices) and V (simplicity)

**Alternatives Considered**:
- **Embedded workers in each service**: Couples task execution with service lifecycle; harder to scale
- **Shared worker pool**: Would work but harder to configure per-service workers
- **Serverless functions (AWS Lambda)**: Not suitable for long-running Celery tasks

**Implementation Details**:
- Worker imports tasks from `common_tasks` module
- Configured with `acks_late=True` for task re-queuing on crash
- Environment variables control concurrency, prefetch, queue names

---

## Decision 5: Configuration Management

**Decision**: Environment variables for all runtime configuration (12-factor app methodology)

**Rationale**:
- No secrets or environment-specific config baked into containers
- Same container image can run in dev, test, prod (only env vars change)
- Docker Compose native support for .env files
- Aligns with modern cloud-native deployment practices
- Easy to override in orchestration platforms (Kubernetes, ECS, etc.)

**Alternatives Considered**:
- **Config files in containers**: Requires rebuilding for config changes; anti-pattern
- **Centralized config service (Consul, etcd)**: Overkill for POC; adds operational complexity
- **Command-line arguments**: Less flexible than env vars; harder to manage at scale

**Environment Variables**:
- `REDIS_BROKER_URL`: Redis connection for Celery broker
- `REDIS_RESULT_BACKEND`: Redis connection for result storage
- Service-specific vars in each `.env.example` file

---

## Decision 6: Containerization Strategy

**Decision**: Docker with multi-stage builds, Docker Compose for local orchestration

**Rationale**:
- Industry standard for containerization
- Multi-stage builds keep images small (build dependencies separate from runtime)
- Docker Compose provides simple local dev environment (no Kubernetes needed for POC)
- Easy migration path to production orchestration (Kubernetes, ECS, Nomad)
- Consistency across development machines

**Alternatives Considered**:
- **Native Python virtual environments**: No isolation between services; can't test deployment
- **Kubernetes locally (minikube, kind)**: Over-engineering for POC; Docker Compose sufficient
- **Podman**: Compatible with Docker but adds learning curve; Docker more familiar

**Docker Decisions**:
- Python 3.11 slim base images (balance size vs. functionality)
- Health checks in Dockerfiles for orchestration readiness
- .dockerignore files to optimize build contexts

---

## Decision 7: Testing Strategy (Deferred for POC)

**Decision**: Minimal testing in POC; comprehensive testing deferred to post-POC

**Rationale**:
- POC focuses on architecture validation, not production reliability
- Constitution testing requirements (integration tests, contract tests, retry tests) add 40-50% effort
- Manual validation sufficient to demonstrate microservices patterns work
- Migration path documented in spec.md for adding tests later

**Deferred Test Types**:
- Contract tests: Validate task signatures between services
- Integration tests: Test task chains across service boundaries
- Retry scenario tests: Verify idempotency and crash recovery
- Load tests: Validate worker scaling characteristics

**POC Validation Approach**:
- Manual smoke tests per user story
- Build verification: All containers build successfully
- Integration check: Task flow from service1 → worker → service2

---

## Decision 8: POC Exemptions from Constitution

**Decision**: Defer Principles II, III, IV to post-POC; implement I and V

**Rationale**:
- **Principle I (Microservices)**: Core to POC - MUST implement
- **Principle II (Idempotency)**: Production concern - defer transaction IDs, comprehensive retries
- **Principle III (Observability)**: Infrastructure concern - defer structured logging, metrics, tracing
- **Principle IV (Error Handling)**: Production concern - defer circuit breakers, DLQs
- **Principle V (Simplicity)**: Core to POC - MUST implement

**Impact**:
- Reduces POC complexity by 40-50%
- Focuses effort on validating core architecture patterns
- Clear migration path documented for production features
- POC still demonstrates value: service isolation, shared tasks, worker scaling, containerization

**Migration Path** (Post-POC):
1. Add idempotency middleware with transaction IDs (Principle II)
2. Integrate structured logging library (structlog) + metrics backend (Prometheus) (Principle III)
3. Add circuit breaker library (pybreaker) + DLQ configuration (Principle IV)
4. Implement comprehensive test suite per constitution testing standards

---

## Open Questions (None)

All technical questions resolved. POC ready for implementation.

---

## References

- Celery Best Practices: https://docs.celeryq.dev/en/stable/userguide/tasks.html#tips-and-best-practices
- 12-Factor App Methodology: https://12factor.net/
- Docker Multi-Stage Builds: https://docs.docker.com/build/building/multi-stage/
- Microservices Patterns: https://microservices.io/
- Python Packaging (pyproject.toml): https://packaging.python.org/en/latest/specifications/pyproject-toml/