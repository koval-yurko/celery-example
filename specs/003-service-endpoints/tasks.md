# Tasks: Service Endpoints for Celery Task Examples

**Input**: Design documents from `/specs/003-service-endpoints/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Tests**: Not requested in specification - implementation tasks only

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Architecture Decision**: `/api/tasks/{task_id}/status`, `/api/tasks/{task_id}/result`, and `/api/tasks/history` endpoints are implemented ONLY in the API Gateway since:
- Both services share the same Redis result backend
- These endpoints query task state/results regardless of which service submitted the task
- Centralizing in the gateway avoids duplication and provides a single interface for all task queries
- Service-specific endpoints (e.g., `/api/tasks/add`, `/api/tasks/multiply`) remain in their respective services

**Implementation Note**: Use Celery native APIs (AsyncResult, Inspect) wherever possible. Direct Redis queries ONLY for task history enumeration and filtering by type, as these capabilities don't exist in Celery's native API (per research findings in research.md).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and verification

- [X] T001 Verify uv workspace configuration in pyproject.toml
- [X] T002 [P] Verify existing FastAPI dependencies in example-service-1/pyproject.toml and example-service-2/pyproject.toml
- [X] T003 [P] Verify existing FastAPI dependencies in api-gateway/pyproject.toml
- [X] T004 [P] Verify Celery worker registration in worker/src/worker/celery_app.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create configurable_outcome_task in common/src/common_tasks/tasks.py with idempotent design
- [X] T006 [P] Create Pydantic request models in example-service-1/src/service1/models.py (AddTaskRequest, LongRunningTaskRequest, ProcessDataRequest)
- [X] T007 [P] Create Pydantic request models in example-service-2/src/service2/models.py (MultiplyTaskRequest, ProgressTaskRequest, ConfigurableOutcomeTaskRequest)
- [X] T008 [P] Create shared response models in api-gateway/src/api_gateway/models.py (TaskSubmissionResponse, TaskStatusResponse, TaskResultResponse, TaskHistoryEntry, TaskHistoryResponse, ErrorResponse)
- [X] T009 Add correlation ID middleware to example-service-1/src/service1/main.py using ContextVar pattern
- [X] T010 Add correlation ID middleware to example-service-2/src/service2/main.py using ContextVar pattern
- [X] T011 Add correlation ID middleware to api-gateway/src/api_gateway/main.py using ContextVar pattern
- [X] T012 [P] Configure custom exception handlers for HTTPException in example-service-1/src/service1/main.py
- [X] T013 [P] Configure custom exception handlers for HTTPException in example-service-2/src/service2/main.py
- [X] T014 [P] Configure custom exception handlers for HTTPException in api-gateway/src/api_gateway/main.py
- [X] T015 Update Celery config in common/src/common_tasks/celery_app.py: set result_expires=None for indefinite retention
- [X] T016 Verify existing task_history.py module in common/src/common_tasks/ uses Redis SCAN (already implemented per research)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic Math Operations via API (Priority: P1) 🎯 MVP

**Goal**: Developers can submit addition/multiplication tasks via HTTP and retrieve results using Celery AsyncResult API

**Independent Test**: Call POST /api/tasks/add with {"x": 4, "y": 6}, get task_id, poll status via API Gateway, retrieve result=10

**Implementation Note**:
- Task submission endpoints: service-specific (service-1 for add, service-2 for multiply)
- Task query endpoints (status/result): centralized in API Gateway (no duplication)

### Implementation for User Story 1

- [X] T017 [P] [US1] Create submit_add_task handler in example-service-1/src/service1/handlers.py using celery_app.send_task()
- [X] T018 [P] [US1] Create submit_multiply_task handler in example-service-2/src/service2/handlers.py using celery_app.send_task()
- [X] T019 [US1] Create get_task_status handler in api-gateway/src/api_gateway/handlers.py using AsyncResult(task_id).state
- [X] T020 [US1] Create get_task_result handler in api-gateway/src/api_gateway/handlers.py using AsyncResult(task_id).get()
- [X] T021 [P] [US1] Implement POST /api/tasks/add endpoint in example-service-1/src/service1/api.py with validation and HTTP 202 response
- [X] T022 [P] [US1] Implement POST /api/tasks/multiply endpoint in example-service-2/src/service2/api.py with validation and HTTP 202 response
- [X] T023 [US1] Implement GET /api/tasks/{task_id}/status endpoint in api-gateway/src/api_gateway/api.py returning TaskStatusResponse
- [X] T024 [US1] Implement GET /api/tasks/{task_id}/result endpoint in api-gateway/src/api_gateway/api.py with 404 error handling
- [X] T025 [US1] Add input validation for numeric parameters with Pydantic in both services
- [X] T026 [US1] Add error handling for invalid task IDs in API Gateway (return 404 with JSON body per FR-012)
- [X] T027 [US1] Add logging with correlation IDs for task submission (services) and queries (gateway)

**Checkpoint**: At this point, basic task submission and result retrieval should work independently for both math operations via the API Gateway

---

## Phase 4: User Story 2 - Long-Running Task Management (Priority: P2)

**Goal**: Developers can submit long-running tasks and poll status without blocking, using Celery AsyncResult for status tracking via API Gateway

**Independent Test**: Submit task with 5-second duration to service-1, immediately get 202 response, poll status via API Gateway showing PENDING→STARTED→SUCCESS transition

**Implementation Note**: Use AsyncResult for status polling in API Gateway. Task stores timestamps in return value (not Celery metadata).

### Implementation for User Story 2

- [X] T028 [US2] Create submit_long_running_task handler in example-service-1/src/service1/handlers.py using celery_app.send_task('long_running_task')
- [X] T029 [US2] Implement POST /api/tasks/long-running endpoint in example-service-1/src/service1/api.py with duration validation (1-300 seconds per FR-015)
- [X] T030 [US2] Update long_running_task in common/src/common_tasks/tasks.py to return timestamps in result dict
- [X] T031 [US2] Verify non-blocking response (HTTP 202) returns within 200ms per SC-001
- [X] T032 [US2] Add logging for long-running task lifecycle (submitted, completed)

**Checkpoint**: Long-running tasks should execute asynchronously with proper state tracking queryable via API Gateway

---

## Phase 5: User Story 5 - Task History and Status Tracking (Priority: P2)

**Goal**: Developers can view complete task history by querying Redis result backend via API Gateway (NOT using Celery native APIs, as enumeration capability doesn't exist)

**Independent Test**: Submit 10+ tasks of different types across both services, call GET /api/tasks/history via API Gateway, verify all tasks listed with states in under 1 second

**Implementation Note**: This is the ONLY feature requiring direct Redis SCAN queries. Implemented ONLY in API Gateway to provide unified task history across all services. Use existing task_history.py module (already implements optimized patterns per research).

### Implementation for User Story 5

- [X] T033 [US5] Create get_task_history handler in api-gateway/src/api_gateway/handlers.py using CeleryTaskHistory.scan_all_tasks_paginated() from common_tasks.task_history
- [X] T034 [US5] Implement GET /api/tasks/history endpoint in api-gateway/src/api_gateway/api.py returning TaskHistoryResponse
- [ ] T035 [US5] Add filtering by task state using TaskTypeFilter.get_tasks_by_status() from task_history module (uses Redis SCAN - no Celery equivalent)
- [ ] T036 [US5] Add filtering by task type using TaskTypeFilter.get_tasks_by_type() from task_history module (uses Redis SCAN - no Celery equivalent)
- [X] T037 [US5] Handle empty task history (return HTTP 200 with empty array per FR-026)
- [ ] T038 [US5] Optimize performance to meet SC-010 (<1 second for 100+ tasks) using OptimizedTaskHistoryQuery with Redis pipelines
- [X] T039 [US5] Add pagination support for large task histories

**Checkpoint**: Task history should enumerate all tasks from all services efficiently using direct Redis access via API Gateway (only feature requiring this)

---

## Phase 6: User Story 6 - Configurable Task Outcome Testing (Priority: P2)

**Goal**: Developers can test both success and failure scenarios, with failed tasks queryable via AsyncResult via API Gateway showing error details

**Independent Test**: Submit task to service-2 with should_succeed=false, verify FAILURE state with error message via API Gateway status endpoint and task history

**Implementation Note**: Use AsyncResult in API Gateway for querying failed tasks (Celery stores traceback). Task history uses Redis SCAN in API Gateway to show all tasks including failures.

### Implementation for User Story 6

- [X] T040 [US6] Create submit_configurable_task handler in example-service-2/src/service2/handlers.py using celery_app.send_task('configurable_outcome_task')
- [X] T041 [US6] Implement POST /api/tasks/configurable endpoint in example-service-2/src/service2/api.py with duration and should_succeed validation
- [X] T042 [US6] Update configurable_outcome_task (T005) to raise exception when should_succeed=False with detailed error message
- [X] T043 [US6] Verify failed tasks return FAILURE state via API Gateway with error message in result.info
- [X] T044 [US6] Update get_task_result handler in API Gateway to include traceback for failed tasks using AsyncResult.traceback
- [X] T045 [US6] Verify task history in API Gateway includes failed tasks with error summaries (uses Redis SCAN from task_history module)
- [X] T046 [US6] Add logging for configurable task outcomes (success and failure cases)

**Checkpoint**: Both success and failure scenarios should be testable with full error visibility via API Gateway

---

## Phase 7: User Story 3 - Progress Tracking for Long Tasks (Priority: P3)

**Goal**: Developers can monitor task progress via API Gateway using AsyncResult.info containing progress metadata

**Independent Test**: Submit progress task with 20 iterations to service-2, poll status via API Gateway showing 0%→50%→100% progression via AsyncResult

**Implementation Note**: Use AsyncResult.info in API Gateway to retrieve progress dict. Task updates state using self.update_state() (Celery native pattern).

### Implementation for User Story 3

- [X] T047 [US3] Create submit_progress_task handler in example-service-2/src/service2/handlers.py using celery_app.send_task('task_with_progress')
- [X] T048 [US3] Implement POST /api/tasks/progress endpoint in example-service-2/src/service2/api.py with iteration validation (1-1000 per FR-016)
- [X] T049 [US3] Update get_task_status handler in API Gateway to extract progress metadata from AsyncResult.info when state='PROGRESS'
- [X] T050 [US3] Verify progress updates visible via API Gateway when polling every 500ms per SC-004
- [X] T051 [US3] Add logging for progress task milestones (0%, 50%, 100%)

**Checkpoint**: Progress tracking should show incremental updates via Celery's native progress mechanism queryable through API Gateway

---

## Phase 8: User Story 4 - Data Processing Tasks (Priority: P3)

**Goal**: Developers can submit JSON payloads for processing and retrieve transformed results via API Gateway using AsyncResult

**Independent Test**: Submit JSON payload (up to 1MB) to service-1, get task_id, retrieve processed result with timestamp via API Gateway

**Implementation Note**: Use AsyncResult in API Gateway for result retrieval. Payload validation uses Pydantic in service-1.

### Implementation for User Story 4

- [X] T052 [US4] Create submit_process_data_task handler in example-service-1/src/service1/handlers.py using celery_app.send_task('process_data')
- [X] T053 [US4] Implement POST /api/tasks/process-data endpoint in example-service-1/src/service1/api.py with JSON validation
- [X] T054 [US4] Add payload size validation (<= 1MB) in ProcessDataRequest model using @model_validator
- [X] T055 [US4] Verify processed results include original input and timestamp per FR-017 (queryable via API Gateway)
- [X] T056 [US4] Add error handling for invalid JSON structure (return 400 with schema details)
- [X] T057 [US4] Add logging for data processing tasks

**Checkpoint**: Data processing should handle large payloads with proper validation, results queryable via API Gateway

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T058 [P] Add worker saturation handling in API Gateway: check Inspect().active() queue depth, return 503 if exceeded (per FR-022)
- [X] T059 [P] Add Redis connection error handling in API Gateway: return 500 when broker unavailable (per FR-013)
- [ ] T060 [P] Add timeout configuration for AsyncResult.get() operations in API Gateway (5 seconds default)
- [ ] T061 [P] Ensure AsyncResult.forget() called after queries in API Gateway to prevent memory leaks
- [X] T062 [P] Add structured logging with correlation IDs across all services and API Gateway
- [X] T063 [P] Add HTTP status code validation: 202 for submission, 200 for queries, 404/500/503 for errors
- [X] T064 Verify result_expires=None in Celery config for indefinite retention (already set in T015)
- [ ] T065 Run quickstart.md validation with curl commands
- [ ] T066 Performance testing: verify SC-001 (<100ms submission), SC-002 (<50ms status via Gateway), SC-010 (<1s history via Gateway)
- [X] T067 Update example-service-1/pyproject.toml, example-service-2/pyproject.toml, and api-gateway/pyproject.toml if new dependencies added

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order: US1 (P1) → US5 (P2) → US6 (P2) → US2 (P2) → US3 (P3) → US4 (P3)
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 - Basic Math Operations (P1)**: MVP - No dependencies on other stories
- **US2 - Long-Running Tasks (P2)**: Independent - Shares status/result endpoints in API Gateway with US1
- **US5 - Task History (P2)**: Independent - Demonstrates result backend enumeration via API Gateway (uses Redis SCAN)
- **US6 - Configurable Outcomes (P2)**: Independent - Tests failure scenarios queryable via API Gateway
- **US3 - Progress Tracking (P3)**: Independent - Uses same patterns as US2 with progress metadata queryable via API Gateway
- **US4 - Data Processing (P3)**: Independent - Uses same patterns as US1 with JSON validation, results via API Gateway

### Architecture: Task Query Endpoints

**Centralized in API Gateway** (NO duplication):
- GET /api/tasks/{task_id}/status (T023) - Works for tasks from any service
- GET /api/tasks/{task_id}/result (T024) - Works for tasks from any service
- GET /api/tasks/history (T034) - Shows tasks from all services

**Service-Specific** (in their respective services):
- POST /api/tasks/add (service-1, T021)
- POST /api/tasks/multiply (service-2, T022)
- POST /api/tasks/long-running (service-1, T029)
- POST /api/tasks/progress (service-2, T048)
- POST /api/tasks/configurable (service-2, T041)
- POST /api/tasks/process-data (service-1, T053)

**Rationale**: Since both services share the same Redis result backend (redis://redis:6379/1), task state/results are accessible from anywhere. Centralizing query endpoints in the API Gateway:
- Eliminates duplication
- Provides a single interface for clients
- Works for tasks from any service (service-agnostic)
- Follows microservices best practices (gateway pattern)

### Celery API Usage Strategy

**Use Celery Native APIs For**:
- Task submission: `celery_app.send_task()` ✅ All user stories (in services)
- Single task status: `AsyncResult(task_id).state` ✅ API Gateway (T019)
- Single task result: `AsyncResult(task_id).get()` ✅ API Gateway (T020)
- Progress metadata: `AsyncResult(task_id).info` ✅ API Gateway (T049)
- Error details: `AsyncResult(task_id).traceback` ✅ API Gateway (T044)
- Worker monitoring: `Inspect().active()` ✅ API Gateway (T058)

**Use Direct Redis ONLY For** (No Celery equivalent exists):
- Task enumeration: `redis.scan("celery-task-meta-*")` ❌ API Gateway (T033) only
- Filter by task type: `TaskTypeFilter.get_tasks_by_type()` ❌ API Gateway (T036) only
- Filter by state: `TaskTypeFilter.get_tasks_by_status()` ❌ API Gateway (T035) only
- Batch queries: `redis.pipeline().get(...).execute()` ❌ API Gateway (T038) only

**Rationale**: Per research.md, Celery intentionally provides no task enumeration APIs to remain backend-agnostic. Direct Redis SCAN is the industry-standard pattern for task history.

### Within Each User Story

- Models before handlers
- Handlers before endpoints
- Core implementation before validation/logging
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks (T001-T004) can run in parallel
- All Foundational model tasks (T006-T008) can run in parallel
- All Foundational middleware tasks (T009-T014) can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Within each story, tasks marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all handler tasks together (different files):
Task T017: "Create submit_add_task handler in example-service-1/src/service1/handlers.py"
Task T018: "Create submit_multiply_task handler in example-service-2/src/service2/handlers.py"

# Launch service-specific endpoints and gateway endpoints together:
Task T021: "Implement POST /api/tasks/add endpoint in example-service-1/src/service1/api.py"
Task T022: "Implement POST /api/tasks/multiply endpoint in example-service-2/src/service2/api.py"
Task T023: "Implement GET /api/tasks/{task_id}/status endpoint in api-gateway/src/api_gateway/api.py"
Task T024: "Implement GET /api/tasks/{task_id}/result endpoint in api-gateway/src/api_gateway/api.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T016) - CRITICAL
3. Complete Phase 3: User Story 1 (T017-T027)
4. **STOP and VALIDATE**: Test math operations independently via API Gateway
5. Deploy/demo basic task submission and retrieval through unified interface

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 (Basic Math) → Test independently via Gateway → Deploy (MVP!)
3. Add US5 (Task History) → Test independently via Gateway → Deploy
4. Add US6 (Failure Testing) → Test independently via Gateway → Deploy
5. Add US2 (Long-Running) → Test independently via Gateway → Deploy
6. Add US3 (Progress) → Test independently via Gateway → Deploy
7. Add US4 (Data Processing) → Test independently via Gateway → Deploy
8. Phase 9: Polish → Final deployment

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done (after T016):
   - Developer A: API Gateway endpoints (T019-T020, T023-T024) + US1 service endpoints
   - Developer B: US5 (Task History in Gateway)
   - Developer C: US6 (Configurable Outcomes)
3. Stories complete and integrate independently through the API Gateway

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **CRITICAL**: Task query endpoints (status/result/history) implemented ONLY in API Gateway to avoid duplication
- Task submission endpoints remain service-specific (domain-driven design)
- Use Celery native APIs in API Gateway wherever possible (AsyncResult, Inspect, send_task)
- Use direct Redis ONLY for task history enumeration in API Gateway (US5) - no Celery equivalent exists
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Total tasks: 67
- MVP scope: Tasks T001-T027 (Setup + Foundational + US1)
- Parallel opportunities: 24 tasks marked [P]
