# Data Model: Service Endpoints for Celery Task Examples

**Feature**: 003-service-endpoints | **Date**: 2025-12-27

## Overview

This document defines the data structures (Pydantic models) for REST API request/response schemas and task parameter/result types. All models use Pydantic v2 for validation and serialization.

## Request Models

### TaskSubmissionRequest (Base Pattern)

All task submission endpoints follow this pattern:

```python
class TaskSubmissionRequest(BaseModel):
    """Base pattern for task submission - not instantiated directly"""
    # Task-specific parameters as fields
    # Examples: operands for math, duration for long-running, etc.
```

### AddTaskRequest

```python
class AddTaskRequest(BaseModel):
    """Addition task submission request"""
    x: int | float = Field(..., description="First operand")
    y: int | float = Field(..., description="Second operand")
```

**Validation Rules**:
- Both x and y must be numeric (int or float)
- No upper/lower bounds (per FR-014)

### MultiplyTaskRequest

```python
class MultiplyTaskRequest(BaseModel):
    """Multiplication task submission request"""
    x: int | float = Field(..., description="First operand")
    y: int | float = Field(..., description="Second operand")
```

**Validation Rules**:
- Both x and y must be numeric (int or float)
- No upper/lower bounds (per FR-014)

### LongRunningTaskRequest

```python
class LongRunningTaskRequest(BaseModel):
    """Long-running task submission request"""
    duration: int = Field(..., ge=1, le=300, description="Duration in seconds")
```

**Validation Rules**:
- duration: integer, range [1, 300] seconds (per FR-015)

### ProgressTaskRequest

```python
class ProgressTaskRequest(BaseModel):
    """Progress-tracked task submission request"""
    iterations: int = Field(..., ge=1, le=1000, description="Number of iterations")
```

**Validation Rules**:
- iterations: integer, range [1, 1000] (per FR-016)

### ProcessDataRequest

```python
class ProcessDataRequest(BaseModel):
    """Data processing task submission request"""
    data: dict[str, Any] = Field(..., description="JSON object to process")

    @model_validator(mode='after')
    def validate_size(self) -> 'ProcessDataRequest':
        # Validate payload size <= 1MB
        import json
        size = len(json.dumps(self.data).encode('utf-8'))
        if size > 1_048_576:  # 1MB
            raise ValueError(f"Payload size {size} bytes exceeds 1MB limit")
        return self
```

**Validation Rules**:
- data: any valid JSON object
- Total serialized size <= 1MB (per acceptance scenario)

### ConfigurableOutcomeTaskRequest

```python
class ConfigurableOutcomeTaskRequest(BaseModel):
    """Configurable outcome task submission request (NEW)"""
    duration: int = Field(..., ge=1, le=300, description="Duration in seconds")
    should_succeed: bool = Field(..., description="True for success, False for failure")
```

**Validation Rules**:
- duration: integer, range [1, 300] seconds
- should_succeed: boolean (per FR-027)

## Response Models

### TaskSubmissionResponse

```python
class TaskSubmissionResponse(BaseModel):
    """Standardized response for task submission (HTTP 202)"""
    status: Literal["accepted"] = Field(..., description="Submission status")
    task_id: str = Field(..., description="Celery task ID (UUID)")
    task_type: str = Field(..., description="Task name/type")
    submitted_at: datetime = Field(..., description="Submission timestamp (ISO 8601)")
    message: str = Field(..., description="Human-readable status message")
```

**Field Details**:
- status: Always "accepted" for successful submissions
- task_id: Celery-generated UUID string
- task_type: e.g., "add", "multiply", "long_running_task", "configurable_outcome_task"
- submitted_at: UTC timestamp in ISO 8601 format
- message: e.g., "Task {task_id} accepted for processing"

### TaskStatusResponse

```python
class TaskStatusResponse(BaseModel):
    """Task status query response (HTTP 200)"""
    task_id: str = Field(..., description="Celery task ID")
    task_type: str | None = Field(None, description="Task name if available")
    state: Literal["PENDING", "STARTED", "PROGRESS", "SUCCESS", "FAILURE", "RETRY", "REVOKED"] = Field(..., description="Current task state")
    progress: dict[str, Any] | None = Field(None, description="Progress metadata (for PROGRESS state)")
    submitted_at: datetime | None = Field(None, description="When task was submitted")
    started_at: datetime | None = Field(None, description="When task started executing")
    completed_at: datetime | None = Field(None, description="When task finished (success or failure)")
```

**Field Details**:
- state: Celery task state enum
- progress: For progress-tracked tasks, contains {current, total, percent}
- Timestamps: Populated from Celery result backend metadata

### TaskResultResponse

```python
class TaskResultResponse(BaseModel):
    """Task result retrieval response (HTTP 200)"""
    task_id: str = Field(..., description="Celery task ID")
    task_type: str | None = Field(None, description="Task name if available")
    state: Literal["SUCCESS", "FAILURE", "PENDING", "STARTED"] = Field(..., description="Final task state")
    result: Any | None = Field(None, description="Task return value (if SUCCESS)")
    error: str | None = Field(None, description="Error message (if FAILURE)")
    traceback: str | None = Field(None, description="Exception traceback (if FAILURE)")
    submitted_at: datetime | None = Field(None, description="Submission timestamp")
    completed_at: datetime | None = Field(None, description="Completion timestamp")
```

**Field Details**:
- result: Task return value for successful tasks (type depends on task)
- error: Exception message for failed tasks (per FR-029)
- traceback: Full Python traceback for failed tasks (per FR-029)

### TaskHistoryEntry

```python
class TaskHistoryEntry(BaseModel):
    """Single task entry in history list"""
    task_id: str = Field(..., description="Celery task ID")
    task_type: str | None = Field(None, description="Task name")
    state: str = Field(..., description="Current state")
    submitted_at: datetime | None = Field(None, description="Submission timestamp")
    completed_at: datetime | None = Field(None, description="Completion timestamp (if finished)")
    result_summary: str | None = Field(None, description="Brief result or error summary")
```

**Field Details**:
- result_summary: For SUCCESS, brief description of result; for FAILURE, error message (per FR-025)

### TaskHistoryResponse

```python
class TaskHistoryResponse(BaseModel):
    """Task history listing response (HTTP 200)"""
    tasks: list[TaskHistoryEntry] = Field(..., description="List of all tasks")
    total_count: int = Field(..., description="Total number of tasks")
    timestamp: datetime = Field(..., description="When history was retrieved")
```

**Field Details**:
- tasks: All tasks from result backend, sorted by submission time (newest first)
- total_count: Number of entries (supports empty list per FR-026)
- timestamp: UTC timestamp when query executed

### ErrorResponse

```python
class ErrorResponse(BaseModel):
    """Standardized error response (HTTP 400/404/500/503)"""
    error: str = Field(..., description="Error type/category")
    message: str = Field(..., description="Human-readable error description")
    details: dict[str, Any] | None = Field(None, description="Additional error context")
    task_id: str | None = Field(None, description="Task ID if applicable (404 errors)")
    timestamp: datetime = Field(..., description="Error occurrence timestamp")
```

**Usage by Status Code**:
- 400: Validation errors (details contains field-level errors)
- 404: Task not found (includes requested task_id per FR-012)
- 500: Internal errors (Redis unavailable per FR-013)
- 503: Service unavailable (worker saturation per FR-022)

## Task Result Types

### Math Operation Results

```python
# Addition/Multiplication tasks return simple numeric results
AddTaskResult = int | float
MultiplyTaskResult = int | float
```

### Long-Running Task Result

```python
class LongRunningTaskResult(TypedDict):
    """Result from long_running_task"""
    message: str  # e.g., "Task completed after 5 seconds"
    duration: int  # Actual duration
    completed_at: float  # Unix timestamp
```

### Progress Task Result

```python
class ProgressTaskResult(TypedDict):
    """Result from task_with_progress"""
    current: int  # Final iteration count
    total: int  # Total iterations
    percent: int  # Always 100 at completion
    status: str  # "Complete"
```

### Process Data Result

```python
class ProcessDataResult(TypedDict):
    """Result from process_data task"""
    input: dict[str, Any]  # Original input data
    processed: bool  # Always True
    timestamp: float  # Processing timestamp (Unix)
```

### Configurable Outcome Task Result

```python
class ConfigurableOutcomeSuccessResult(TypedDict):
    """Result when configurable task succeeds"""
    message: str  # e.g., "Task succeeded after 10 seconds"
    duration: int  # Configured duration
    outcome: Literal["success"]
    completed_at: float  # Unix timestamp

# On failure, task raises exception (no success result)
# Exception message stored in Celery result backend
```

## Entity Relationships

```
TaskSubmissionRequest → Celery Task → TaskSubmissionResponse
                                           ↓
                                      Result Backend
                                           ↓
                         TaskStatusResponse / TaskResultResponse
                                           ↓
                                    TaskHistoryEntry
                                           ↓
                                  TaskHistoryResponse
```

**Flow**:
1. Client sends TaskSubmissionRequest → API validates → Celery task dispatched
2. API returns TaskSubmissionResponse (HTTP 202) with task_id
3. Task executes → state/results stored in Result Backend
4. Client polls TaskStatusResponse or retrieves TaskResultResponse by task_id
5. Task history aggregates all TaskHistoryEntry records from Result Backend

## Validation Strategy

### Request Validation
- Pydantic validates all requests before task submission
- Return 400 with field-level errors for validation failures
- No invalid data reaches Celery workers

### Response Consistency
- All timestamps use UTC timezone with ISO 8601 format
- All task_id fields are UUID strings (Celery format)
- state fields use Celery's canonical state names

### Error Handling
- Use ErrorResponse model for all error responses (400/404/500/503)
- Include correlation IDs in logs (not in response model for simplicity)
- Never expose internal stack traces in API responses (only in failed task traceback field)

## Storage Considerations

### Result Backend Schema
- Celery stores tasks in Redis with key pattern: `celery-task-meta-{task_id}`
- Task metadata includes: state, result, traceback, date_done, children
- Custom metadata (task_type, submitted_at) stored in task args/kwargs or result

### History Retrieval Strategy
- Scan Redis keys matching `celery-task-meta-*` pattern
- Retrieve metadata for each task ID
- Filter/sort in application layer (Redis scan is unordered)
- Performance: O(N) where N = total tasks; acceptable for 100+ tasks per SC-010

### Indefinite Retention
- Redis persistence configured to never expire task results (per FR-021)
- No TTL on `celery-task-meta-*` keys
- Manual cleanup required for production (out of scope per spec)
