# Quickstart Guide: Service Endpoints for Celery Task Examples

**Feature**: 003-service-endpoints | **Date**: 2025-12-27

## Overview

This guide shows developers how to use the new HTTP endpoints that expose Celery task functionality through service-1 and service-2.

## Prerequisites

- Services running via docker-compose or locally
- Redis broker and result backend accessible
- Celery workers running

## Quick Start

### 1. Start the Services

```bash
# Start all services with docker-compose
docker-compose up

# Or run services locally
cd example-service-1 && uvicorn service1.main:app --port 8001 &
cd example-service-2 && uvicorn service2.main:app --port 8002 &
cd worker && celery -A worker.celery_app worker --loglevel=info &
```

### 2. Submit a Task

```bash
# Submit addition task to service-1
curl -X POST http://localhost:8001/api/tasks/add \
  -H "Content-Type: application/json" \
  -d '{"x": 10, "y": 5}'

# Response (HTTP 202):
{
  "status": "accepted",
  "task_id": "abc123-def456-...",
  "task_type": "add",
  "submitted_at": "2025-12-27T10:30:00Z",
  "message": "Task abc123... accepted for processing"
}
```

### 3. Check Task Status (via API Gateway)

```bash
# Query task status through API Gateway (works for tasks from ANY service)
curl http://localhost:8000/api/tasks/abc123-def456-.../status

# Response while running:
{
  "task_id": "abc123-def456-...",
  "task_type": "add",
  "state": "STARTED",
  "progress": null,
  "submitted_at": "2025-12-27T10:30:00Z",
  "started_at": "2025-12-27T10:30:01Z",
  "completed_at": null
}

# Response when complete:
{
  "task_id": "abc123-def456-...",
  "task_type": "add",
  "state": "SUCCESS",
  "progress": null,
  "submitted_at": "2025-12-27T10:30:00Z",
  "started_at": "2025-12-27T10:30:01Z",
  "completed_at": "2025-12-27T10:30:02Z"
}
```

### 4. Get Task Result (via API Gateway)

```bash
# Retrieve task result through API Gateway (works for tasks from ANY service)
curl http://localhost:8000/api/tasks/abc123-def456-.../result

# Response:
{
  "task_id": "abc123-def456-...",
  "task_type": "add",
  "state": "SUCCESS",
  "result": 15,
  "error": null,
  "traceback": null,
  "submitted_at": "2025-12-27T10:30:00Z",
  "completed_at": "2025-12-27T10:30:02Z"
}
```

### 5. View Task History (via API Gateway)

```bash
# Get all tasks through API Gateway (returns tasks from ALL services)
curl http://localhost:8000/api/tasks/history

# Response:
{
  "tasks": [
    {
      "task_id": "abc123...",
      "task_type": "add",
      "state": "SUCCESS",
      "submitted_at": "2025-12-27T10:30:00Z",
      "completed_at": "2025-12-27T10:30:02Z",
      "result_summary": "15"
    },
    ...
  ],
  "total_count": 42,
  "timestamp": "2025-12-27T11:00:00Z"
}
```

## Available Endpoints

### API Gateway (Port 8000) - Task Query Endpoints

**Centralized endpoints for querying tasks from ALL services:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks/{task_id}/status` | Get task status (any service) |
| GET | `/api/tasks/{task_id}/result` | Get task result (any service) |
| GET | `/api/tasks/history` | Get all tasks (with filtering) |

**Query Parameters for `/api/tasks/history`:**
- `limit` - Maximum tasks to return (default: 100)
- `offset` - Number of tasks to skip (default: 0)
- `task_type` - Filter by task type (e.g., 'add', 'multiply')
- `state` - Filter by state (e.g., 'SUCCESS', 'FAILURE', 'PENDING')

### Service-1 (Port 8001) - Task Submission

**Task submission endpoints (accessed via API Gateway at `/api/service1/*`):**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tasks/add` | Submit addition task |
| POST | `/api/tasks/long-running` | Submit long-running task |
| POST | `/api/tasks/process-data` | Submit data processing task |

### Service-2 (Port 8002) - Task Submission

**Task submission endpoints (accessed via API Gateway at `/api/service2/*`):**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tasks/multiply` | Submit multiplication task |
| POST | `/api/tasks/progress` | Submit progress-tracked task |
| POST | `/api/tasks/configurable` | Submit configurable outcome task |

## Example Workflows

### Basic Math Operations

```bash
# Addition
curl -X POST http://localhost:8001/api/tasks/add \
  -d '{"x": 42, "y": 8}' -H "Content-Type: application/json"

# Multiplication
curl -X POST http://localhost:8002/api/tasks/multiply \
  -d '{"x": 7, "y": 6}' -H "Content-Type: application/json"
```

### Long-Running Task with Progress

```bash
# Submit progress task (20 iterations) via API Gateway
TASK_ID=$(curl -X POST http://localhost:8000/api/service2/tasks/progress \
  -d '{"iterations": 20}' -H "Content-Type: application/json" \
  | jq -r '.task_id')

# Poll for progress via API Gateway
while true; do
  curl http://localhost:8000/api/tasks/$TASK_ID/status | jq '.progress'
  sleep 1
done
```

### Test Success and Failure Scenarios

```bash
# Submit task configured to succeed via API Gateway
curl -X POST http://localhost:8000/api/service2/tasks/configurable \
  -d '{"duration": 5, "should_succeed": true}' \
  -H "Content-Type: application/json"

# Submit task configured to fail via API Gateway
curl -X POST http://localhost:8000/api/service2/tasks/configurable \
  -d '{"duration": 3, "should_succeed": false}' \
  -H "Content-Type: application/json"

# Check failure details via API Gateway
curl http://localhost:8000/api/tasks/$TASK_ID/result
# Returns error message and traceback
```

### Data Processing

```bash
# Submit complex data
curl -X POST http://localhost:8001/api/tasks/process-data \
  -d '{"data": {"user": "alice", "action": "login", "timestamp": 1234567890}}' \
  -H "Content-Type: application/json"
```

## Error Handling

### 400 - Validation Error

```bash
# Invalid input (non-numeric)
curl -X POST http://localhost:8001/api/tasks/add \
  -d '{"x": "abc", "y": 5}'

# Response:
{
  "error": "validation_error",
  "message": "Invalid input parameters",
  "details": {
    "field": "x",
    "error": "Input should be a valid number"
  },
  "timestamp": "2025-12-27T10:00:00Z"
}
```

### 404 - Task Not Found

```bash
# Query non-existent task
curl http://localhost:8001/api/tasks/invalid-id/status

# Response:
{
  "error": "task_not_found",
  "message": "Task not found in result backend",
  "task_id": "invalid-id",
  "timestamp": "2025-12-27T10:00:00Z"
}
```

### 503 - Service Unavailable

```bash
# When workers are saturated
curl -X POST http://localhost:8001/api/tasks/add -d '{"x": 1, "y": 2}'

# Response:
{
  "error": "service_unavailable",
  "message": "Workers at capacity, please retry",
  "timestamp": "2025-12-27T10:00:00Z"
}
```

## Testing Tips

1. **Use correlation IDs** for tracking:
   ```bash
   curl -H "X-Correlation-ID: my-test-123" ...
   ```

2. **Filter task history** by state and/or type via API Gateway:
   ```bash
   # Filter by state only
   curl "http://localhost:8000/api/tasks/history?state=FAILURE"

   # Filter by task type only
   curl "http://localhost:8000/api/tasks/history?task_type=add"

   # Filter by both state and type
   curl "http://localhost:8000/api/tasks/history?task_type=multiply&state=SUCCESS"

   # Pagination
   curl "http://localhost:8000/api/tasks/history?limit=50&offset=100"
   ```

3. **Monitor Redis**:
   ```bash
   redis-cli -n 1 KEYS "celery-task-meta-*" | wc -l
   ```

4. **Check worker status**:
   ```bash
   celery -A worker.celery_app inspect active
   celery -A worker.celery_app inspect stats
   ```

## Next Steps

- See [OpenAPI specs](contracts/) for complete API documentation
- Review [data-model.md](data-model.md) for request/response schemas
- Check [plan.md](plan.md) for implementation details
