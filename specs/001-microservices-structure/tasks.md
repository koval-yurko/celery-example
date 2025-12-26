# Tasks: Microservices Repository Structure

**Input**: Design documents from `/specs/001-microservices-structure/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are NOT explicitly requested in the specification, so test tasks are not included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This is a **monorepo** with services at root level (per FR-014, Constitution v1.1.0):
- **Root**: `.venv/` (single virtual environment), `pyproject.toml` (workspace config), `uv.lock` (lock file)
- **common/**: Shared task definitions
- **worker/**: Dedicated worker service
- **example-service-1/**, **example-service-2/**: Business services
- Services follow pattern: `{service-name}/src/{service-name}/`
- **uv** MUST be used for all dependency management (FR-018)
- **NO** `sys.path.insert()` - standard Python imports only (FR-016)
- **ALL routes in api.py** - no dynamic route loading (FR-017)

---

## POC Scope: Simplified Implementation

This task list implements a **proof-of-concept (POC)** focused on demonstrating core Celery microservices patterns. Production-grade features from Constitution Principles II, III, and IV are **intentionally deferred** to post-POC iterations.

### Implemented in POC
✅ Microservices architecture with task queue communication (Principle I)
✅ Service isolation with independent deployment
✅ Shared task definitions via common module
✅ Dedicated worker services
✅ Containerized deployment with Docker
✅ Basic Celery configuration (acks_late, simple retry)
✅ Simplicity-first approach (Principle V)

### Deferred to Post-POC (Not in Task List)
🔜 **Idempotency & Reliability** (Principle II): Unique transaction IDs, comprehensive retry policies with exponential backoff
🔜 **Monitoring & Observability** (Principle III): Structured JSON logging, task lifecycle events, metrics collection, correlation IDs
🔜 **Error Handling & Resilience** (Principle IV): Circuit breakers, dead letter queues, sophisticated error classification
🔜 **Testing**: Integration tests for task chains, contract tests for signatures, retry scenario tests

**Migration Path**: See spec.md "POC Exemptions from Constitution" section for detailed migration strategy.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, monorepo configuration, and basic structure per FR-014 to FR-019, Constitution v1.1.0

- [x] T001 Setup project infrastructure: Create root directory structure (common/, worker/, example-service-1/, example-service-2/), global .env.example with Redis connection variables, and README.md with architecture overview
- [x] T002 Configure monorepo with uv workspace (FR-014, FR-015, FR-018): Create root pyproject.toml with uv workspace configuration declaring all packages (common, worker, example-service-1, example-service-2), run `uv sync` to generate uv.lock file (FR-019), verify single .venv at root level only

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core shared infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Setup common module structure: Initialize common/pyproject.toml (Python 3.11+, Celery 5.3+, pydantic), create common/src/common_tasks/ package with __init__.py, create common/tests/ directory
- [x] T004 Implement common module core: Create celery_app.py (Celery config with Redis broker), schemas.py (Pydantic base models), tasks.py (placeholder task definitions)
- [x] T005 Setup infrastructure orchestration: Create docker-compose.yml at repository root with Redis service definition and network configuration

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Service Isolation (Priority: P1) 🎯 MVP

**Goal**: Enable running and testing individual services in complete isolation so developers can work on one service without requiring all other services to be running

**Independent Test**: Build and run example-service-1 in isolation, send it a request, verify it responds correctly without any other services running

### Implementation for User Story 1

- [x] T006 [P] [US1] Setup example-service-1 structure: Initialize pyproject.toml (Python 3.11+, common_tasks dependency), create src/service1/ package with __init__.py, .env.example with service-specific variables, tests/ directory
- [x] T007 [P] [US1] Implement example-service-1 logic: Create main.py (service initialization), api.py (ALL routes per FR-017), handlers.py (task publishers for queue communication)
- [x] T008 [P] [US1] Setup example-service-2 structure: Initialize pyproject.toml (Python 3.11+, common_tasks dependency), create src/service2/ package with __init__.py, .env.example with service-specific variables, tests/ directory
- [x] T009 [P] [US1] Implement example-service-2 logic: Create main.py (service initialization), api.py (ALL routes per FR-017), handlers.py (task consumers from queues)

**Checkpoint**: At this point, User Story 1 should be fully functional - both services can run independently with their own dependencies

---

## Phase 4: User Story 2 - Shared Task Definitions (Priority: P2)

**Goal**: Enable accessing common task definitions and shared utilities across all services so services can communicate through standardized task contracts without duplicating code

**Independent Test**: Import common module from two different services, verify both can call shared task definitions, confirm changes to common code are immediately available to all services after rebuild

### Implementation for User Story 2

- [x] T010 [US2] Define shared task contracts: Implement standardized task definitions in common/src/common_tasks/tasks.py (process_order, send_notification), create Pydantic schemas in schemas.py (OrderPayload, NotificationPayload), document contracts in common/README.md
- [x] T011 [US2] Integrate shared tasks in services: Update example-service-1/handlers.py and example-service-2/handlers.py to use shared task definitions from common module (using standard imports per FR-016), add task result handling in service1/api.py using common schemas

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - services are isolated AND share standardized task definitions

---

## Phase 5: User Story 3 - Dedicated Task Workers (Priority: P3)

**Goal**: Enable dedicated worker services that exclusively execute tasks so task processing can be scaled independently from business services and resource-intensive task execution is isolated

**Independent Test**: Deploy only worker services (no business services), publish tasks to queue externally, verify workers consume and execute tasks successfully

### Implementation for User Story 3

- [x] T012 [US3] Setup worker service structure: Initialize worker/pyproject.toml (Python 3.11+, Celery 5.3+, common_tasks dependency), create worker/src/worker/ package with __init__.py, .env.example with worker-specific configuration (concurrency, queue names, prefetch settings)
- [x] T013 [US3] Implement worker service: Create config.py (worker configuration with acks_late=True and retry policies), main.py (Celery worker startup script that imports tasks from common_tasks using standard imports per FR-016), update docker-compose.yml to include worker service definition

**Checkpoint**: All user stories 1, 2, and 3 should now work - services are isolated, share task definitions, AND have dedicated workers

---

## Phase 6: User Story 4 - Containerized Deployment (Priority: P4)

**Goal**: Enable building and running each service using standardized container instructions so environments are consistent across development, testing, and production

**Independent Test**: Build a service container from scratch on a clean machine, run it, verify it operates identically to development environments

### Implementation for User Story 4

- [x] T014 [P] [US4] Create Dockerfiles for all services: Create common/Dockerfile (multi-stage build with Python 3.11), worker/Dockerfile, example-service-1/Dockerfile, example-service-2/Dockerfile - all with common module installation and proper base images
- [x] T015 [US4] Configure docker-compose orchestration: Update docker-compose.yml to include all services (Redis, worker, example-service-1, example-service-2) with proper networking, environment variable injection from .env file, and service dependencies
- [x] T016 [US4] Add container health checks and documentation: Add health checks to all Dockerfiles for container orchestration, create .dockerignore files for each service to optimize build contexts, document container build and run instructions in README.md

**Checkpoint**: All user stories should now be independently functional and containerized

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [x] T017 [P] Add logging and error handling: Implement comprehensive logging configuration across all services (common, worker, service1, service2), add basic error handling and validation across all service endpoints
- [x] T018 Validate all user stories: Test service isolation (run one service while others stopped), validate shared task definitions (execute cross-service task flow), validate worker scaling (run multiple worker instances and measure throughput), verify `uv sync` works correctly (SC-010), verify imports work without sys.path.insert (SC-009)
- [x] T019 Final documentation and verification: Update CLAUDE.md with final tech stack and project structure, build all containers from scratch and run full docker-compose stack, verify all success criteria from spec.md including SC-011 (reproducible environments via uv.lock)
- [x] T020 [US1] Refactor example-service-2 to use separate api.py (FR-017): Create example-service-2/src/service2/api.py with FastAPI router containing all HTTP routes, update main.py to import and include the router, move any route definitions from main.py/handlers.py to api.py for consistency with example-service-1 pattern

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (Service Isolation) can start immediately after Foundational
  - US2 (Shared Task Definitions) depends on US1 (needs services to integrate with)
  - US3 (Dedicated Workers) depends on US2 (needs shared task definitions to execute)
  - US4 (Containerized Deployment) can start in parallel with US3 but depends on US1, US2, US3 for complete testing
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

```
Phase 2 (Foundational)
    ↓
Phase 3 (US1: Service Isolation)
    ↓
Phase 4 (US2: Shared Task Definitions)
    ↓
Phase 5 (US3: Dedicated Workers)
    ↓ (can overlap)
Phase 6 (US4: Containerized Deployment)
    ↓
Phase 7 (Polish)
```

### Within Each User Story

- **US1**: Tasks T005-T006 and T007-T008 can run in parallel (different services)
- **US2**: Tasks must be sequential (shared definitions → service integration)
- **US3**: Tasks must be sequential (setup → implementation)
- **US4**: T013 creates all Dockerfiles in parallel, then T014-T015 sequential

### Parallel Opportunities

- **Phase 2**: T002 and T003 can run in parallel (different files in common module)
- **Phase 3 (US1)**:
  - T005 and T007 can run in parallel (different services)
  - T006 and T008 can run in parallel (different services)
- **Phase 6 (US4)**: T013 creates all Dockerfiles in parallel

---

## Parallel Example: User Story 1

```bash
# Launch both service setup tasks together:
Task: "Setup example-service-1 structure"
Task: "Setup example-service-2 structure"

# Then launch both implementation tasks together:
Task: "Implement example-service-1 logic"
Task: "Implement example-service-2 logic"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002-T004) - CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (T005-T008)
4. **STOP and VALIDATE**: Test service isolation independently
5. Demo/review before continuing

**MVP Deliverable**: Two isolated services that can run independently with their own dependencies, communicating via task queues

### Incremental Delivery

1. **Foundation** (Phases 1-2): Setup + common module → Foundation ready (4 tasks)
2. **Iteration 1** (Phase 3): Add US1 → Test independently → Demo (4 tasks, MVP!)
   - Deliverable: Isolated services running independently
3. **Iteration 2** (Phase 4): Add US2 → Test independently → Demo (2 tasks)
   - Deliverable: Services sharing standardized task definitions
4. **Iteration 3** (Phase 5): Add US3 → Test independently → Demo (2 tasks)
   - Deliverable: Dedicated workers for scalable task processing
5. **Iteration 4** (Phase 6): Add US4 → Test independently → Demo (3 tasks)
   - Deliverable: Fully containerized deployment
6. **Final Polish** (Phase 7): Cross-cutting concerns → Final validation (3 tasks)

Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. **Team completes Setup + Foundational together** (Phases 1-2)
2. Once Foundational is done:
   - **Developer A**: T005-T006 (Service 1)
   - **Developer B**: T007-T008 (Service 2)
3. After US1 completes:
   - **Developer A**: US2 (Shared Task Definitions) - Phase 4
   - **Developer B**: Start T013 (Dockerfiles) from Phase 6
4. After US2 completes:
   - **Developer A**: US3 (Dedicated Workers) - Phase 5
   - **Developer B**: Continue US4 docker-compose work
5. Final integration and validation together

---

## Task Summary

**Total Tasks**: 20 (T001-T020)
- **Phase 1 (Setup)**: 2 tasks (T001-T002, includes uv workspace setup)
- **Phase 2 (Foundational)**: 3 tasks (T003-T005, BLOCKING)
- **Phase 3 (US1 - Service Isolation)**: 4 tasks (T006-T009, 2 pairs parallelizable)
- **Phase 4 (US2 - Shared Task Definitions)**: 2 tasks (T010-T011)
- **Phase 5 (US3 - Dedicated Workers)**: 2 tasks (T012-T013)
- **Phase 6 (US4 - Containerized Deployment)**: 3 tasks (T014-T016, first parallelizable)
- **Phase 7 (Polish)**: 4 tasks (T017-T020, T020 for FR-017 compliance)

**New Tasks Added (Constitution v1.1.0)**:
- T002: Configure monorepo with uv workspace (FR-014, FR-015, FR-018, FR-019)

**Parallelization Opportunities**: 7 tasks marked [P] can run in parallel

**MVP Scope** (Recommended first delivery):
- Phase 1: Setup (2 tasks including uv workspace)
- Phase 2: Foundational (3 tasks)
- Phase 3: User Story 1 (4 tasks)
- **Total MVP**: 9 tasks

---

## Task Consolidation Details

**Merged from original 52 tasks**:
- **Setup**: 3 tasks → 1 task (directory structure + .env + README combined)
- **Foundational**: 7 tasks → 3 tasks (grouped by common module setup, implementation, infrastructure)
- **US1**: 13 tasks → 4 tasks (grouped by service: setup + implementation per service)
- **US2**: 6 tasks → 2 tasks (define contracts, integrate in services)
- **US3**: 7 tasks → 2 tasks (setup worker, implement worker)
- **US4**: 8 tasks → 3 tasks (all Dockerfiles, docker-compose, health checks + docs)
- **Polish**: 8 tasks → 3 tasks (logging + error handling, validation, final docs)

**Benefits of consolidation**:
- 65% reduction in task count (52 → 18)
- Fewer context switches between related files
- Clearer logical grouping of work
- Each task is still atomic and committable
- Maintains all user story checkpoints
- Preserves parallelization opportunities

---

## Notes

- **[P] tasks**: Different files/services, no dependencies - can run in parallel
- **[Story] label**: Maps task to specific user story for traceability and independent testing
- Each user story should be independently completable and testable
- Commit after each task completion
- Stop at any checkpoint to validate story independently
- **POC Focus**: This is a proof-of-concept implementation - simplicity is prioritized over production-grade features
- **Constitution Alignment**: Implements Constitution Principles I & V; Principles II, III, IV deferred per documented POC exemptions (see spec.md)
- **Consolidated Tasks**: Related work merged into single tasks for efficiency while maintaining atomicity and clear deliverables