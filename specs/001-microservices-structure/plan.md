# Implementation Plan: Microservices Repository Structure

**Branch**: `001-microservices-structure` | **Date**: 2025-12-25 | **Spec**: [spec.md](spec.md)

## Summary

Restructure the repository to support a microservices architecture using Celery for inter-service communication. This is a POC focused on exploring Celery microservices patterns with simplicity prioritized over production-grade features.

**Technical Approach**: Create isolated service directories with Docker containerization, a shared common module for task definitions, and a dedicated worker service for task execution. Services communicate exclusively via Redis/Celery task queues.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Celery 5.3+, Redis 7.0+, Docker 24.0+, Docker Compose 2.20+
**Storage**: Redis (message broker and result backend)
**Testing**: pytest
**Target Platform**: Docker containers (Linux-based)
**Project Type**: Microservices POC
**Constraints**: POC simplicity, same common module version across all services, environment variable configuration only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Microservices Architecture ✅ PASS
Services communicate via Celery task queues with shared common module for task definitions.

### Principle II: Task Idempotency & Reliability ⚠️ POC EXEMPTION
- **Deferred**: Production-grade idempotency (unique transaction IDs, duplicate detection)
- **Deferred**: Comprehensive retry policies with exponential backoff
- **POC Implementation**: Basic acks_late=True configuration and simple retry logic
- **Justification**: POC focuses on validating architecture patterns, not production reliability

### Principle III: Monitoring & Observability ⚠️ POC EXEMPTION
- **Deferred**: Structured JSON logging, task lifecycle events, metrics collection, correlation IDs
- **POC Implementation**: Basic print/log statements for debugging
- **Justification**: Observability infrastructure adds 30-40% complexity not needed to demonstrate microservices patterns

### Principle IV: Error Handling & Resilience ⚠️ POC EXEMPTION
- **Deferred**: Circuit breakers, dead letter queues, sophisticated error classification
- **POC Implementation**: Basic exception handling with Celery's built-in retry mechanism
- **Justification**: POC demonstrates happy-path task execution; production resilience deferred to post-POC

### Principle V: Simplicity First ✅ PASS
Minimal service set, standard Python packaging, no over-engineering. POC exemptions align with simplicity principle.

**Gate Status**: ✅ **PASSED** (with documented POC exemptions per spec.md)

## Project Structure

### Documentation (this feature)

```text
specs/001-microservices-structure/
├── plan.md              # This file
├── research.md          # Phase 0: Architecture decisions
├── data-model.md        # Phase 1: Task payload schemas
├── quickstart.md        # Phase 1: Quick start guide
└── contracts/           # Phase 1: Task contracts (Celery signatures)
```

### Source Code (repository root)

```text
common/                      # Shared task definitions and utilities
├── pyproject.toml
├── src/
│   └── common_tasks/
│       ├── __init__.py
│       ├── tasks.py        # Task definitions
│       ├── schemas.py      # Pydantic models
│       └── celery_app.py   # Celery configuration
└── tests/

worker/                      # Dedicated Celery worker service
├── Dockerfile
├── pyproject.toml
├── src/
│   └── worker/
│       ├── __init__.py
│       ├── main.py         # Worker startup
│       └── config.py
└── .env.example

example-service-1/           # Example business service (order-service)
├── Dockerfile
├── pyproject.toml
├── src/
│   └── service1/
│       ├── __init__.py
│       ├── main.py
│       ├── api.py
│       └── handlers.py
├── tests/
└── .env.example

example-service-2/           # Example business service (notification-service)
├── Dockerfile
├── pyproject.toml
├── src/
│   └── service2/
│       ├── __init__.py
│       ├── main.py
│       └── handlers.py
├── tests/
└── .env.example

# Infrastructure
docker-compose.yml           # Local orchestration (Redis + all services)
.env.example                 # Global environment variables
README.md

# Existing (preserved)
app.py
Dockerfile
pyproject.toml
```

**Key Decisions**:
- No services/ wrapper folder - services at root level
- Docker Compose for local orchestration
- Environment variable configuration (12-factor app)
- Same common module version across all services (per Clarification Q1)

## Complexity Tracking

**No violations** - POC exemptions explicitly documented in spec.