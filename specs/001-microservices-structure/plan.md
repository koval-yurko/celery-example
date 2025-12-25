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
**Dependency Management**: `uv` (per Constitution v1.1.0)

## Monorepo Architecture

### Core Constraints (per FR-014 to FR-019, Constitution v1.1.0)

1. **Single Virtual Environment**
   - Location: `.venv/` at repository root only
   - Services MUST NOT have individual virtual environments
   - All local development uses the shared root `.venv`

2. **uv as Dependency Tool** (Constitution v1.1.0)
   - `uv` MUST be used for all dependency operations
   - `uv sync` installs all workspace packages
   - `uv.lock` MUST be generated and committed for reproducible builds

3. **Centralized Dependency Management**
   - Root `pyproject.toml` defines workspace with all packages
   - Single `uv sync` from root installs everything
   - Service-level `pyproject.toml` files define container-specific dependencies only

4. **Explicit Path Resolution (No sys.path.insert)**
   - All imports MUST use standard Python package resolution
   - Common module installed as editable package: `uv pip install -e ./common`
   - NO runtime path manipulation (`sys.path.insert()` forbidden)
   - Import pattern: `from common_tasks.tasks import process_order`

5. **API Route Organization**
   - Routes MUST remain in each service's `api.py` file
   - Routes MUST NOT be dynamically loaded or split across files
   - Pattern: All endpoints defined in `service/api.py`

### Dependency Installation Strategy

**Local Development (root .venv)**:
```bash
# Create single virtual environment at root
uv venv

# Install all packages including services as editable
uv sync

# Or with pip compatibility
uv pip install -e ./common -e ./worker -e ./example-service-1 -e ./example-service-2

# Verify installation
python -c "from common_tasks.tasks import process_order; print('OK')"
```

**Container Build (Dockerfile)**:
```dockerfile
# Each service Dockerfile copies and installs common + service
COPY common/ /app/common/
COPY example-service-1/ /app/example-service-1/
RUN pip install /app/common /app/example-service-1
```

### Import Resolution Example

```python
# example-service-1/src/service1/api.py

# CORRECT - Standard package import (package installed in .venv)
from common_tasks.tasks import process_order
from common_tasks.schemas import OrderPayload

# FORBIDDEN - No sys.path manipulation
# import sys
# sys.path.insert(0, '../../common/src')  # NOT ALLOWED
```

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
# Monorepo Root (FR-014, FR-015, FR-018, FR-019)
.venv/                       # SINGLE virtual environment (root only)
pyproject.toml               # Root: declares all workspace packages
uv.lock                      # Lock file for reproducible installs (FR-019)

common/                      # Shared task definitions and utilities
├── pyproject.toml           # Package metadata (installed in root .venv)
├── src/
│   └── common_tasks/
│       ├── __init__.py
│       ├── tasks.py         # Task definitions
│       ├── schemas.py       # Pydantic models
│       └── celery_app.py    # Celery configuration
└── tests/

worker/                      # Dedicated Celery worker service
├── Dockerfile
├── pyproject.toml           # Container-specific dependencies
├── src/
│   └── worker/
│       ├── __init__.py
│       ├── main.py          # Worker startup
│       └── config.py
└── .env.example

example-service-1/           # Example business service (order-service)
├── Dockerfile
├── pyproject.toml           # Container-specific dependencies
├── src/
│   └── service1/
│       ├── __init__.py
│       ├── main.py
│       ├── api.py           # ALL routes here (FR-017)
│       └── handlers.py
├── tests/
└── .env.example

example-service-2/           # Example business service (notification-service)
├── Dockerfile
├── pyproject.toml           # Container-specific dependencies
├── src/
│   └── service2/
│       ├── __init__.py
│       ├── main.py
│       ├── api.py           # ALL routes here (FR-017)
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
```

**Key Decisions**:
- **Monorepo with single .venv at root** (per FR-014) - no per-service virtual environments
- **uv for dependency management** (per FR-018, Constitution v1.1.0)
- **uv.lock for reproducible builds** (per FR-019)
- Root `pyproject.toml` with workspace configuration (per FR-015)
- No services/ wrapper folder - services at root level
- Docker Compose for local orchestration
- Environment variable configuration (12-factor app)
- Same common module version across all services (per Clarification Q1)
- **No sys.path.insert()** - explicit package installation (per FR-016)
- **Routes in api.py only** - no dynamic route loading (per FR-017)

## Complexity Tracking

**No violations** - POC exemptions explicitly documented in spec.