# Feature Specification: Service Endpoints for Celery Task Examples

**Feature Branch**: `003-service-endpoints`
**Created**: 2025-12-27
**Status**: Draft
**Input**: User description: "add new endpoints to service-1 and service-2 to cover examples provided on @celery_example/main.py file"

## Clarifications

### Session 2025-12-27

- Q: How long should task results be retained before they expire or are cleaned up? → A: Indefinite - Results persist until manually deleted
- Q: When a non-existent task ID is queried, should the API return just an error code or include detailed error information? → A: Standard - HTTP 404 with JSON error body containing error message and task ID
- Q: When all workers are busy and new task requests arrive, how should the API respond? → A: Timeout-based - API waits briefly for worker availability, then returns 503 if none available
- Q: Can we use Celery backend for task history storage? → A: Yes - Added requirements for task history endpoints and configurable success/failure tasks to demonstrate result backend capabilities

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Math Operations via API (Priority: P1)

Developers need to execute simple arithmetic operations (addition and multiplication) through HTTP endpoints to demonstrate basic task submission and retrieval patterns in a microservices architecture.

**Why this priority**: This represents the fundamental building block for task-based APIs - submitting a task, getting a task ID, and retrieving results. All other patterns build on this foundation.

**Independent Test**: Can be fully tested by calling POST endpoints with numeric parameters and retrieving results via task ID, demonstrating complete request-response cycle.

**Acceptance Scenarios**:

1. **Given** service-1 is running, **When** a developer sends an addition request with two numbers (e.g., 4 and 6), **Then** the service returns a task ID and the developer can retrieve the result (10)
2. **Given** service-2 is running, **When** a developer sends a multiplication request with two numbers (e.g., 5 and 8), **Then** the service returns a task ID and the developer can retrieve the result (40)
3. **Given** a task has been submitted, **When** the developer checks task status before completion, **Then** the service returns current state (PENDING, STARTED, etc.)
4. **Given** invalid input is provided (non-numeric values), **When** the request is submitted, **Then** the service returns a 400 error with validation message

---

### User Story 2 - Long-Running Task Management (Priority: P2)

Developers need to submit long-running tasks without blocking the API response, check task status asynchronously, and understand task lifecycle states for building responsive applications.

**Why this priority**: Essential for real-world async patterns but doesn't block basic functionality. Teaches developers how to handle operations that take significant time.

**Independent Test**: Can be tested by submitting a task with configurable duration, immediately receiving acknowledgment, and polling status until completion.

**Acceptance Scenarios**:

1. **Given** service-1 exposes a long-running endpoint, **When** a developer submits a task with 5-second duration, **Then** the API returns immediately (within 200ms) with a task ID
2. **Given** a long-running task is executing, **When** the developer polls the status endpoint, **Then** the service returns task state (PENDING, STARTED, SUCCESS) without waiting for completion
3. **Given** a long-running task completes, **When** the developer retrieves the result, **Then** the service returns the completion message and timestamp
4. **Given** multiple long-running tasks are submitted concurrently, **When** the developer tracks each by task ID, **Then** each task executes independently without interference

---

### User Story 3 - Progress Tracking for Long Tasks (Priority: P3)

Developers need to monitor real-time progress of iterative tasks to build progress bars and user feedback mechanisms in their applications.

**Why this priority**: Enhances user experience but not critical for basic async task functionality. Represents advanced pattern.

**Independent Test**: Can be tested by submitting a task with known iteration count and polling to verify progressive percentage updates.

**Acceptance Scenarios**:

1. **Given** service-2 exposes a progress-tracked endpoint, **When** a developer submits a task with 20 iterations, **Then** the API returns a task ID immediately
2. **Given** a progress-tracked task is running, **When** the developer polls the task status, **Then** the service returns current progress percentage (0-100%)
3. **Given** a task is at 50% progress, **When** the developer continues polling, **Then** subsequent calls show increasing percentages until 100%
4. **Given** a task completes, **When** the developer retrieves final results, **Then** the service returns 100% completion status with final payload

---

### User Story 4 - Data Processing Tasks (Priority: P3)

Developers need to submit structured data payloads for processing and receive transformed results to demonstrate data transformation patterns.

**Why this priority**: Common pattern but builds on basic task submission. Can be delayed until foundational endpoints are working.

**Independent Test**: Can be tested by submitting JSON payloads and verifying processed output includes original data plus processing metadata.

**Acceptance Scenarios**:

1. **Given** service-1 exposes a data processing endpoint, **When** a developer submits a JSON object with name and value fields, **Then** the service returns a task ID
2. **Given** a data processing task completes, **When** the developer retrieves results, **Then** the response includes original input, processing timestamp, and processed flag
3. **Given** invalid JSON structure is submitted, **When** the request is processed, **Then** the service returns a 400 error with schema validation details
4. **Given** large data payloads (up to 1MB), **When** submitted for processing, **Then** the service handles them without memory errors

---

### User Story 5 - Task History and Status Tracking (Priority: P2)

Developers need to view the complete history of all submitted tasks across services to understand system behavior, debug issues, and monitor task execution patterns over time.

**Why this priority**: Essential for demonstrating task lifecycle management and debugging capabilities. Shows how the result backend stores task history persistently.

**Independent Test**: Can be tested by submitting multiple tasks of different types, then querying the task history endpoint to verify all tasks are listed with their current states and metadata.

**Acceptance Scenarios**:

1. **Given** multiple tasks have been submitted across service-1 and service-2, **When** a developer requests task history, **Then** the service returns a list of all tasks with their IDs, types, states, and submission timestamps
2. **Given** tasks in different states (PENDING, SUCCESS, FAILURE) exist, **When** a developer views task history, **Then** each task shows its current state and relevant metadata
3. **Given** a task history with 100+ tasks, **When** a developer requests the list, **Then** the service returns the results in a reasonable timeframe (under 1 second)
4. **Given** no tasks have been submitted yet, **When** a developer requests task history, **Then** the service returns an empty list with HTTP 200

---

### User Story 6 - Configurable Task Outcome Testing (Priority: P2)

Developers need to test both successful and failed task scenarios to understand error handling, demonstrate failure recovery patterns, and verify that task state transitions work correctly for both outcomes.

**Why this priority**: Critical for demonstrating complete task lifecycle including failure scenarios. Essential for teaching developers how to handle task errors and build resilient applications.

**Independent Test**: Can be tested by submitting tasks configured to succeed or fail, then verifying the task state and error information in both the status endpoint and task history.

**Acceptance Scenarios**:

1. **Given** service-2 exposes a configurable outcome endpoint, **When** a developer submits a task configured to succeed after duration, **Then** the task completes with SUCCESS state and returns a success message
2. **Given** service-2 exposes a configurable outcome endpoint, **When** a developer submits a task configured to fail after duration, **Then** the task completes with FAILURE state and returns error details
3. **Given** a task configured to fail, **When** the developer queries task status after completion, **Then** the service returns FAILURE state with error message and traceback information
4. **Given** multiple success and failure tasks in history, **When** a developer views task history, **Then** both successful and failed tasks are visible with their respective states and outcomes

---

### Edge Cases

- When a task ID that doesn't exist is queried, the system returns HTTP 404 with a JSON error body containing the error message and the requested task ID
- When concurrent requests exceed available workers, the API waits briefly for a worker to become available, then returns HTTP 503 (Service Unavailable) if the timeout expires
- What happens if Redis broker becomes unavailable during task submission?
- How are tasks handled if they exceed maximum allowed execution time?
- What happens when result backend storage fills up?
- How does the system respond to malformed task parameters after task is enqueued?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Service-1 MUST provide an endpoint to submit addition tasks accepting two numeric parameters
- **FR-002**: Service-1 MUST provide an endpoint to submit long-running tasks with configurable duration parameter
- **FR-003**: Service-1 MUST provide an endpoint to submit data processing tasks accepting JSON payloads
- **FR-004**: Service-2 MUST provide an endpoint to submit multiplication tasks accepting two numeric parameters
- **FR-005**: Service-2 MUST provide an endpoint to submit progress-tracked tasks with configurable iteration count
- **FR-023**: Service-2 MUST provide an endpoint to submit configurable outcome tasks accepting duration and success/failure flag parameters
- **FR-024**: Both services MUST provide an endpoint to retrieve task history listing all submitted tasks
- **FR-006**: Both services MUST return task IDs immediately upon task submission without waiting for completion
- **FR-007**: Both services MUST provide endpoints to query task status by task ID
- **FR-008**: Both services MUST provide endpoints to retrieve task results by task ID
- **FR-021**: Task results MUST persist indefinitely in the result backend until manually deleted
- **FR-009**: Task status endpoints MUST return current task state (PENDING, STARTED, PROGRESS, SUCCESS, FAILURE)
- **FR-010**: Progress-tracked tasks MUST return percentage completion (0-100%) when queried during execution
- **FR-011**: All endpoints MUST validate input parameters and return 400 errors for invalid inputs
- **FR-012**: Result retrieval endpoints MUST return 404 errors with JSON error body (containing error message and task ID) when task IDs don't exist
- **FR-013**: All endpoints MUST return 500 errors with appropriate messages when broker/backend is unavailable
- **FR-022**: Task submission endpoints MUST wait briefly for worker availability when all workers are busy, then return HTTP 503 (Service Unavailable) if no workers become available within the timeout period
- **FR-014**: Addition and multiplication endpoints MUST support integer and floating-point numbers
- **FR-015**: Long-running task endpoint MUST accept duration in seconds (integer, 1-300 range)
- **FR-016**: Progress-tracked task endpoint MUST accept iteration count (integer, 1-1000 range)
- **FR-017**: Data processing endpoint MUST accept JSON objects and return processed results with timestamp
- **FR-018**: All task submission endpoints MUST return HTTP 202 (Accepted) status code
- **FR-019**: Task result endpoints MUST return HTTP 200 with results when task is complete
- **FR-020**: Task status endpoints MUST return HTTP 200 with current state regardless of task completion
- **FR-025**: Task history endpoints MUST return a list of all tasks with task ID, task type, current state, submission timestamp, and completion timestamp (if completed)
- **FR-026**: Task history endpoints MUST support empty results (HTTP 200 with empty array when no tasks exist)
- **FR-027**: Configurable outcome tasks MUST accept a boolean parameter indicating success (true) or failure (false)
- **FR-028**: Configurable outcome tasks configured to fail MUST raise an exception after the specified duration and store error details in the result backend
- **FR-029**: Failed tasks MUST be queryable via status and result endpoints showing FAILURE state with error message and traceback
- **FR-030**: Task history MUST include both successful and failed tasks with their respective final states

### Key Entities

- **Task Submission Request**: Contains task type, input parameters, and optional configuration (duration, iterations, success/failure flag); triggers async task creation
- **Task Response**: Contains task ID, submission status, and timestamp; returned immediately upon task submission
- **Task Status**: Represents current task state (PENDING, STARTED, PROGRESS, SUCCESS, FAILURE) with optional metadata like progress percentage
- **Task Result**: Contains final output from completed task, including original input, processed data, timestamps, and success/failure indicators; for failed tasks includes error message and traceback
- **Task History Entry**: Contains task ID, task type/name, current state, submission timestamp, completion timestamp (if completed), and final result or error summary
- **Error Response**: JSON object containing error message and relevant context (e.g., task ID for 404 errors, validation details for 400 errors)
- **Math Operation Task**: Simple computation task with two numeric operands and an operator type (add or multiply)
- **Long-Running Task**: Time-based task with duration parameter and completion message
- **Progress Task**: Iterative task with progress tracking metadata (current iteration, total iterations, percentage)
- **Data Processing Task**: Transformation task accepting structured JSON input and returning processed output
- **Configurable Outcome Task**: Time-based task with duration parameter and success/failure flag; succeeds with completion message or fails with exception and error details

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can submit tasks and receive task IDs in under 100ms (95th percentile)
- **SC-002**: Task status queries return results in under 50ms (95th percentile)
- **SC-003**: All task types (add, multiply, long-running, progress-tracked, data processing, configurable outcome) execute successfully
- **SC-004**: Progress tracking updates are visible when polling every 500ms during task execution
- **SC-005**: System handles 100 concurrent task submissions without errors
- **SC-006**: Invalid inputs are rejected with clear error messages in 100% of validation test cases
- **SC-007**: Developers can retrieve completed task results within 200ms after task completion
- **SC-008**: All endpoints return appropriate HTTP status codes (202, 200, 400, 404, 500, 503) matching REST conventions
- **SC-009**: When all workers are busy, task submission responds with 503 within defined timeout period (prevents indefinite blocking)
- **SC-010**: Task history retrieval returns results in under 1 second for 100+ task entries
- **SC-011**: Failed tasks appear in task history with FAILURE state and error information visible
- **SC-012**: Configurable outcome tasks configured to fail properly transition to FAILURE state with accessible error details

## Assumptions *(if applicable)*

- Celery workers are already configured and running in the environment
- Redis broker and result backend are available and accessible to both services
- Redis result backend is configured to store task state, results, and metadata indefinitely
- Task timeout limits are configured at the Celery worker level (not enforced by API)
- Result backend has sufficient storage for expected task volume and indefinite history retention
- Services use existing Celery task definitions from celery_example.tasks module
- API endpoints follow RESTful conventions established in current service implementations
- Error handling matches patterns used in existing service endpoints
- Both services run independently and can be deployed separately
- Task IDs are generated by Celery (UUIDs) and managed by the framework
- Task history is retrieved by querying the Celery result backend (not a separate database)
- No authentication/authorization is required for these demonstration endpoints

## Dependencies *(if applicable)*

- Existing Celery task implementations (add, multiply, long_running_task, task_with_progress, process_data)
- Redis broker must be running and accessible
- Celery workers must be configured to consume tasks from appropriate queues
- FastAPI framework and routing infrastructure in both services
- Pydantic models for request/response validation
- Existing health check endpoints should remain functional

## Out of Scope

- Task cancellation or termination functionality
- Task prioritization or queue management features
- Webhook notifications on task completion
- Task retry configuration through API
- Batch task submission endpoints
- Task result pagination or filtering
- Task scheduling or delayed execution through API
- Authentication or authorization for endpoints
- Rate limiting or throttling
- Automatic task result expiration or cleanup (results persist indefinitely)
- Custom task routing or worker selection
- Task chain or workflow composition endpoints
