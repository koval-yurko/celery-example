# Tasks: Service Endpoints for Celery Task Examples

**Input**: Design documents from `/specs/003-service-endpoints/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Tests**: Not requested in specification - implementation tasks only

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Implementation Note**: Use Celery native APIs (AsyncResult, Inspect) wherever possible. Direct Redis queries ONLY for task history enumeration and filtering by type, as these capabilities don't exist in Celery's native API (per research findings in [CELERY_RESEARCH_FINDINGS.md](../../CELERY_RESEARCH_FINDINGS.md)).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and verification

- [ ] T001 Verify uv workspace configuration in pyproject.toml
- [ ] T002 [P] Verify existing FastAPI dependencies in example-service-1/pyproject.toml and example-service-2/pyproject.toml
- [ ] T003 [P] Verify Celery worker registration in worker/src/worker/celery_app.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create configurable_outcome_task in common/src/common_tasks/tasks.py with idempotent design
- [ ] T005 [P] Create Pydantic request models in example-service-1/src/service1/models.py (AddTaskRequest, LongRunningTaskRequest, ProcessDataRequest)
- [ ] T006 [P] Create Pydantic request models in example-service-2/src/service2/models.py (MultiplyTaskRequest, ProgressTaskRequest, ConfigurableOutcomeTaskRequest)
- [ ] T007 [P] Create shared response models in example-service-1/src/service1/models.py (TaskSubmissionResponse, TaskStatusResponse, TaskResultResponse)
- [ ] T008 [P] Create shared response models in example-service-2/src/service2/models.py (TaskSubmissionResponse, TaskStatusResponse, TaskResultResponse)
- [ ] T009 [P] Create ErrorResponse model in example-service-1/src/service1/models.py
- [ ] T010 [P] Create ErrorResponse model in example-service-2/src/service2/models.py
- [ ] T011 Create TaskHistoryEntry and TaskHistoryResponse models in example-service-1/src/service1/models.py
- [ ] T012 Create TaskHistoryEntry and TaskHistoryResponse models in example-service-2/src/service2/models.py
- [ ] T013 Add correlation ID middleware to example-service-1/src/service1/main.py using ContextVar pattern
- [ ] T014 Add correlation ID middleware to example-service-2/src/service2/main.py using ContextVar pattern
- [ ] T015 [P] Configure custom exception handlers for HTTPException in example-service-1/src/service1/main.py
- [ ] T016 [P] Configure custom exception handlers for HTTPException in example-service-2/src/service2/main.py
- [ ] T017 Update Celery config in common/src/common_tasks/celery_app.py: set result_expires=None for indefinite retention
- [ ] T018 Verify existing task_history.py module in common/src/common_tasks/ uses Redis SCAN (already implemented per research)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic Math Operations via API (Priority: P1) 🎯 MVP

**Goal**: Developers can submit addition/multiplication tasks via HTTP and retrieve results using Celery AsyncResult API

**Independent Test**: Call POST /api/tasks/add with {"x": 4, "y": 6}, get task_id, poll status using Celery AsyncResult, retrieve result=10

**Implementation Note**: Use Celery's AsyncResult API for status/result queries (single task operations). NO direct Redis access needed.

### Implementation for User Story 1

- [ ] T019 [P] [US1] Create submit_add_task handler in example-service-1/src/service1/handlers.py using celery_app.send_task()
- [ ] T020 [P] [US1] Create submit_multiply_task handler in example-service-2/src/service2/handlers.py using celery_app.send_task()
- [ ] T021 [P] [US1] Create get_task_status handler in example-service-1/src/service1/handlers.py using AsyncResult(task_id).state
- [ ] T022 [P] [US1] Create get_task_status handler in example-service-2/src/service2/handlers.py using AsyncResult(task_id).state
- [ ] T023 [P] [US1] Create get_task_result handler in example-service-1/src/service1/handlers.py using AsyncResult(task_id).get()
- [ ] T024 [P] [US1] Create get_task_result handler in example-service-2/src/service2/handlers.py using AsyncResult(task_id).get()
- [ ] T025 [P] [US1] Implement POST /api/tasks/add endpoint in example-service-1/src/service1/api.py with validation and HTTP 202 response
- [ ] T026 [P] [US1] Implement POST /api/tasks/multiply endpoint in example-service-2/src/service2/api.py with validation and HTTP 202 response
- [ ] T027 [P] [US1] Implement GET /api/tasks/{task_id}/status endpoint in example-service-1/src/service1/api.py returning TaskStatusResponse
- [ ] T028 [P] [US1] Implement GET /api/tasks/{task_id}/status endpoint in example-service-2/src/service2/api.py returning TaskStatusResponse
- [ ] T029 [P] [US1] Implement GET /api/tasks/{task_id}/result endpoint in example-service-1/src/service1/api.py with 404 error handling
- [ ] T030 [P] [US1] Implement GET /api/tasks/{task_id}/result endpoint in example-service-2/src/service2/api.py with 404 error handling
- [ ] T031 [US1] Add input validation for numeric parameters with Pydantic in both services
- [ ] T032 [US1] Add error handling for invalid task IDs (return 404 with JSON body per FR-012)
- [ ] T033 [US1] Add logging with correlation IDs for task submission and queries

**Checkpoint**: At this point, basic task submission and result retrieval should work independently for both math operations

---

## Phase 4: User Story 2 - Long-Running Task Management (Priority: P2)

**Goal**: Developers can submit long-running tasks and poll status without blocking, using Celery AsyncResult for status tracking

**Independent Test**: Submit task with 5-second duration, immediately get 202 response, poll status showing PENDING→STARTED→SUCCESS transition

**Implementation Note**: Use AsyncResult for status polling. Task stores timestamps in return value (not Celery metadata).

### Implementation for User Story 2

- [ ] T034 [US2] Create submit_long_running_task handler in example-service-1/src/service1/handlers.py using celery_app.send_task('long_running_task')
- [ ] T035 [US2] Implement POST /api/tasks/long-running endpoint in example-service-1/src/service1/api.py with duration validation (1-300 seconds per FR-015)
- [ ] T036 [US2] Update long_running_task in common/src/common_tasks/tasks.py to return timestamps in result dict
- [ ] T037 [US2] Verify non-blocking response (HTTP 202) returns within 200ms per SC-001
- [ ] T038 [US2] Add logging for long-running task lifecycle (submitted, completed)

**Checkpoint**: Long-running tasks should execute asynchronously with proper state tracking

---

## Phase 5: User Story 5 - Task History and Status Tracking (Priority: P2)

**Goal**: Developers can view complete task history by querying Redis result backend (NOT using Celery native APIs, as enumeration capability doesn't exist)

**Independent Test**: Submit 10+ tasks of different types, call GET /api/tasks/history, verify all tasks listed with states in under 1 second

**Implementation Note**: This is the ONLY feature requiring direct Redis SCAN queries. Use existing task_history.py module (already implements optimized patterns per research).

### Implementation for User Story 5

- [ ] T039 [P] [US5] Create get_task_history handler in example-service-1/src/service1/handlers.py using CeleryTaskHistory.scan_all_tasks_paginated() from common_tasks.task_history
- [ ] T040 [P] [US5] Create get_task_history handler in example-service-2/src/service2/handlers.py using CeleryTaskHistory.scan_all_tasks_paginated() from common_tasks.task_history
- [ ] T041 [P] [US5] Implement GET /api/tasks/history endpoint in example-service-1/src/service1/api.py returning TaskHistoryResponse
- [ ] T042 [P] [US5] Implement GET /api/tasks/history endpoint in example-service-2/src/service2/api.py returning TaskHistoryResponse
- [ ] T043 [US5] Add filtering by task state using TaskTypeFilter.get_tasks_by_status() from task_history module (uses Redis SCAN - no Celery equivalent)
- [ ] T044 [US5] Add filtering by task type using TaskTypeFilter.get_tasks_by_type() from task_history module (uses Redis SCAN - no Celery equivalent)
- [ ] T045 [US5] Handle empty task history (return HTTP 200 with empty array per FR-026)
- [ ] T046 [US5] Optimize performance to meet SC-010 (<1 second for 100+ tasks) using OptimizedTaskHistoryQuery with Redis pipelines
- [ ] T047 [US5] Add pagination support for large task histories

**Checkpoint**: Task history should enumerate all tasks efficiently using direct Redis access (only feature requiring this)

---

## Phase 6: User Story 6 - Configurable Task Outcome Testing (Priority: P2)

**Goal**: Developers can test both success and failure scenarios, with failed tasks queryable via AsyncResult showing error details

**Independent Test**: Submit task with should_succeed=false, verify FAILURE state with error message via AsyncResult.info and task history

**Implementation Note**: Use AsyncResult for querying failed tasks (Celery stores traceback). Task history uses Redis SCAN to show all tasks including failures.

### Implementation for User Story 6

- [ ] T048 [US6] Create submit_configurable_task handler in example-service-2/src/service2/handlers.py using celery_app.send_task('configurable_outcome_task')
- [ ] T049 [US6] Implement POST /api/tasks/configurable endpoint in example-service-2/src/service2/api.py with duration and should_succeed validation
- [ ] T050 [US6] Update configurable_outcome_task (T004) to raise exception when should_succeed=False with detailed error message
- [ ] T051 [US6] Verify failed tasks return FAILURE state via AsyncResult with error message in result.info
- [ ] T052 [US6] Update get_task_result handler to include traceback for failed tasks using AsyncResult.traceback
- [ ] T053 [US6] Verify task history includes failed tasks with error summaries (uses Redis SCAN from task_history module)
- [ ] T054 [US6] Add logging for configurable task outcomes (success and failure cases)

**Checkpoint**: Both success and failure scenarios should be testable with full error visibility

---

## Phase 7: User Story 3 - Progress Tracking for Long Tasks (Priority: P3)

**Goal**: Developers can monitor task progress via AsyncResult.info containing progress metadata

**Independent Test**: Submit progress task with 20 iterations, poll status showing 0%→50%→100% progression via AsyncResult

**Implementation Note**: Use AsyncResult.info to retrieve progress dict. Task updates state using self.update_state() (Celery native pattern).

### Implementation for User Story 3

- [ ] T055 [US3] Create submit_progress_task handler in example-service-2/src/service2/handlers.py using celery_app.send_task('task_with_progress')
- [ ] T056 [US3] Implement POST /api/tasks/progress endpoint in example-service-2/src/service2/api.py with iteration validation (1-1000 per FR-016)
- [ ] T057 [US3] Update get_task_status handler to extract progress metadata from AsyncResult.info when state='PROGRESS'
- [ ] T058 [US3] Verify progress updates visible when polling every 500ms per SC-004
- [ ] T059 [US3] Add logging for progress task milestones (0%, 50%, 100%)

**Checkpoint**: Progress tracking should show incremental updates via Celery's native progress mechanism

---

## Phase 8: User Story 4 - Data Processing Tasks (Priority: P3)

**Goal**: Developers can submit JSON payloads for processing and retrieve transformed results via AsyncResult

**Independent Test**: Submit JSON payload (up to 1MB), get task_id, retrieve processed result with timestamp

**Implementation Note**: Use AsyncResult for result retrieval. Payload validation uses Pydantic.

### Implementation for User Story 4

- [ ] T060 [US4] Create submit_process_data_task handler in example-service-1/src/service1/handlers.py using celery_app.send_task('process_data')
- [ ] T061 [US4] Implement POST /api/tasks/process-data endpoint in example-service-1/src/service1/api.py with JSON validation
- [ ] T062 [US4] Add payload size validation (<= 1MB) in ProcessDataRequest model using @model_validator
- [ ] T063 [US4] Verify processed results include original input and timestamp per FR-017
- [ ] T064 [US4] Add error handling for invalid JSON structure (return 400 with schema details)
- [ ] T065 [US4] Add logging for data processing tasks

**Checkpoint**: Data processing should handle large payloads with proper validation

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T066 [P] Add worker saturation handling: check Inspect().active() queue depth, return 503 if exceeded (per FR-022)
- [ ] T067 [P] Add Redis connection error handling: return 500 when broker unavailable (per FR-013)
- [ ] T068 [P] Add timeout configuration for AsyncResult.get() operations (5 seconds default)
- [ ] T069 [P] Ensure AsyncResult.forget() called after queries to prevent memory leaks
- [ ] T070 [P] Add structured logging with correlation IDs across all endpoints
- [ ] T071 [P] Add HTTP status code validation: 202 for submission, 200 for queries, 404/500/503 for errors
- [ ] T072 Verify result_expires=None in Celery config for indefinite retention (already set in T017)
- [ ] T073 Run quickstart.md validation with curl commands
- [ ] T074 Performance testing: verify SC-001 (<100ms submission), SC-002 (<50ms status), SC-010 (<1s history)
- [ ] T075 Update example-service-1/pyproject.toml and example-service-2/pyproject.toml if new dependencies added

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
- **US2 - Long-Running Tasks (P2)**: Independent - Shares status/result endpoints with US1
- **US5 - Task History (P2)**: Independent - Demonstrates result backend enumeration (uses Redis SCAN)
- **US6 - Configurable Outcomes (P2)**: Independent - Tests failure scenarios
- **US3 - Progress Tracking (P3)**: Independent - Uses same patterns as US2 with progress metadata
- **US4 - Data Processing (P3)**: Independent - Uses same patterns as US1 with JSON validation

### Celery API Usage Strategy

**Use Celery Native APIs For**:
- Task submission: `celery_app.send_task()` ✅ All user stories
- Single task status: `AsyncResult(task_id).state` ✅ US1, US2, US3, US4, US6
- Single task result: `AsyncResult(task_id).get()` ✅ US1, US2, US3, US4, US6
- Progress metadata: `AsyncResult(task_id).info` ✅ US3
- Error details: `AsyncResult(task_id).traceback` ✅ US6
- Worker monitoring: `Inspect().active()` ✅ Phase 9 (saturation check)

**Use Direct Redis ONLY For** (No Celery equivalent exists):
- Task enumeration: `redis.scan("celery-task-meta-*")` ❌ US5 only
- Filter by task type: `TaskTypeFilter.get_tasks_by_type()` ❌ US5 only
- Filter by state: `TaskTypeFilter.get_tasks_by_status()` ❌ US5 only
- Batch queries: `redis.pipeline().get(...).execute()` ❌ US5 only (optimization)

**Rationale**: Per [CELERY_RESEARCH_FINDINGS.md](../../CELERY_RESEARCH_FINDINGS.md), Celery intentionally provides no task enumeration APIs to remain backend-agnostic. Direct Redis SCAN is the industry-standard pattern for task history.

### Within Each User Story

- Models before handlers
- Handlers before endpoints
- Core implementation before validation/logging
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks (T001-T003) can run in parallel
- All Foundational model tasks (T005-T012) can run in parallel
- All Foundational middleware tasks (T013-T016) can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Within each story, tasks marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all handler tasks together (different files):
Task T019: "Create submit_add_task handler in example-service-1/src/service1/handlers.py"
Task T020: "Create submit_multiply_task handler in example-service-2/src/service2/handlers.py"
Task T021: "Create get_task_status handler in example-service-1/src/service1/handlers.py"
Task T022: "Create get_task_status handler in example-service-2/src/service2/handlers.py"

# Launch all endpoint tasks together (different functions in same file):
Task T025: "Implement POST /api/tasks/add endpoint in example-service-1/src/service1/api.py"
Task T026: "Implement POST /api/tasks/multiply endpoint in example-service-2/src/service2/api.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T018) - CRITICAL
3. Complete Phase 3: User Story 1 (T019-T033)
4. **STOP and VALIDATE**: Test math operations independently
5. Deploy/demo basic task submission and retrieval

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 (Basic Math) → Test independently → Deploy (MVP!)
3. Add US5 (Task History) → Test independently → Deploy
4. Add US6 (Failure Testing) → Test independently → Deploy
5. Add US2 (Long-Running) → Test independently → Deploy
6. Add US3 (Progress) → Test independently → Deploy
7. Add US4 (Data Processing) → Test independently → Deploy
8. Phase 9: Polish → Final deployment

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done (after T018):
   - Developer A: US1 (Basic Math)
   - Developer B: US5 (Task History)
   - Developer C: US6 (Configurable Outcomes)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Use Celery native APIs wherever possible (AsyncResult, Inspect, send_task)
- Use direct Redis ONLY for task history enumeration (US5) - no Celery equivalent exists
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Total tasks: 75
- MVP scope: Tasks T001-T033 (Setup + Foundational + US1)
- Parallel opportunities: 28 tasks marked [P]
