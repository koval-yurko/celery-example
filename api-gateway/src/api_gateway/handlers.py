"""
Task Query Handlers for API Gateway

Centralized handlers for querying task status, results, and history from
the shared Redis result backend. These handlers work for tasks submitted
by any service since all services share the same Redis backend.
"""

import logging
import os
from datetime import datetime
from typing import Optional

from celery.result import AsyncResult
from fastapi import HTTPException

from .models import TaskStatusResponse, TaskResultResponse, TaskHistoryResponse, TaskHistoryEntry

logger = logging.getLogger(__name__)

# Get Celery app instance
# Import from common_tasks which is accessible via uv workspace
try:
    from common_tasks.celery_app import celery_app
except ImportError:
    logger.warning("Could not import celery_app from common_tasks, task query features will not work")
    celery_app = None

# Worker saturation threshold (configurable via environment variable)
MAX_ACTIVE_TASKS_PER_WORKER = int(os.getenv("MAX_ACTIVE_TASKS_PER_WORKER", "10"))

# Default timeout for AsyncResult.get() operations (configurable via environment variable)
DEFAULT_RESULT_TIMEOUT = float(os.getenv("CELERY_RESULT_TIMEOUT", "5.0"))


def check_worker_saturation() -> None:
    """
    Check if workers are saturated (too many active tasks).

    Uses Celery Inspect API to check active task count across all workers.
    Raises 503 if workers are overloaded to prevent task queue overflow.

    Raises:
        HTTPException: 503 if workers are saturated
    """
    if not celery_app:
        return  # Skip check if Celery unavailable

    try:
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()

        if not active_tasks:
            # No workers available or no tasks running
            return

        # Count total active tasks across all workers
        total_active = sum(len(tasks) for tasks in active_tasks.values())
        num_workers = len(active_tasks)

        # Check if saturated (more than threshold)
        threshold = MAX_ACTIVE_TASKS_PER_WORKER * num_workers
        if total_active >= threshold:
            logger.warning(
                f"Workers saturated: {total_active} active tasks across {num_workers} workers (threshold: {threshold})"
            )
            raise HTTPException(
                status_code=503,
                detail=f"Workers are currently saturated ({total_active} active tasks). Please try again later."
            )

    except HTTPException:
        raise  # Re-raise 503 errors
    except Exception as e:
        logger.error(f"Error checking worker saturation: {e}")
        # Don't fail requests if we can't check saturation


def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    Query task status using Celery AsyncResult API.

    Args:
        task_id: Celery task ID (UUID)

    Returns:
        TaskStatusResponse with current task state and metadata

    Raises:
        HTTPException: 404 if task not found, 500 if Celery unavailable
    """
    if not celery_app:
        logger.error("Celery app not available")
        raise HTTPException(status_code=500, detail="Task query service unavailable")

    try:
        result = AsyncResult(task_id, app=celery_app)

        # Extract task state
        state = result.state

        # Extract progress metadata if available (for PROGRESS state)
        progress = None
        if state == "PROGRESS" and result.info:
            if isinstance(result.info, dict):
                progress = result.info

        # Build response
        response = TaskStatusResponse(
            task_id=task_id,
            task_type=result.name if hasattr(result, 'name') else None,
            state=state,
            progress=progress,
            submitted_at=None,  # Not available from AsyncResult
            started_at=None,    # Not available from AsyncResult
            completed_at=None   # Not available from AsyncResult
        )

        logger.info(
            f"Task status queried: {task_id}",
            extra={"task_id": task_id, "state": state}
        )

        # Clean up result object to prevent memory leaks
        try:
            result.forget()
        except Exception as e:
            logger.warning(f"Failed to forget result for task {task_id}: {e}")

        return response

    except Exception as e:
        logger.error(f"Error querying task status: {e}", extra={"task_id": task_id})
        raise HTTPException(
            status_code=500,
            detail=f"Error querying task status: {str(e)}"
        )


def get_task_result(task_id: str, timeout: Optional[float] = None) -> TaskResultResponse:
    """
    Query task result using Celery AsyncResult API.

    Args:
        task_id: Celery task ID (UUID)
        timeout: Optional timeout in seconds (default: 5 seconds from env CELERY_RESULT_TIMEOUT)

    Returns:
        TaskResultResponse with task result or error details

    Raises:
        HTTPException: 404 if task not found, 500 if Celery unavailable
    """
    if not celery_app:
        logger.error("Celery app not available")
        raise HTTPException(status_code=500, detail="Task query service unavailable")

    try:
        result = AsyncResult(task_id, app=celery_app)

        # Use default timeout if not specified
        effective_timeout = timeout if timeout is not None else DEFAULT_RESULT_TIMEOUT

        # Get current state
        state = result.state

        # Determine result or error
        task_result = None
        error_msg = None
        traceback_str = None

        if state == "SUCCESS":
            task_result = result.result
        elif state == "FAILURE":
            # Get error details
            error_msg = str(result.info) if result.info else "Task failed"
            traceback_str = result.traceback
        elif state in ["PENDING", "STARTED", "PROGRESS"]:
            # Task not yet complete
            pass

        response = TaskResultResponse(
            task_id=task_id,
            task_type=result.name if hasattr(result, 'name') else None,
            state=state,
            result=task_result,
            error=error_msg,
            traceback=traceback_str,
            submitted_at=None,  # Not available from AsyncResult
            completed_at=None   # Not available from AsyncResult
        )

        logger.info(
            f"Task result queried: {task_id}",
            extra={"task_id": task_id, "state": state}
        )

        # Clean up result object to prevent memory leaks
        try:
            result.forget()
        except Exception as e:
            logger.warning(f"Failed to forget result for task {task_id}: {e}")

        return response

    except Exception as e:
        logger.error(f"Error querying task result: {e}", extra={"task_id": task_id})
        raise HTTPException(
            status_code=500,
            detail=f"Error querying task result: {str(e)}"
        )


def get_task_history(
    limit: int = 100,
    offset: int = 0,
    task_type: Optional[str] = None,
    state: Optional[str] = None
) -> TaskHistoryResponse:
    """
    Get task history from Redis result backend with optional filtering.

    This function uses direct Redis SCAN because Celery doesn't provide
    a native API for enumerating all tasks (by design, to remain backend-agnostic).

    Args:
        limit: Maximum number of tasks to return
        offset: Number of tasks to skip
        task_type: Optional filter by task type/name
        state: Optional filter by task state (PENDING, SUCCESS, FAILURE, etc.)

    Returns:
        TaskHistoryResponse with list of all tasks

    Raises:
        HTTPException: 500 if query fails
    """
    try:
        # Import task history module from common_tasks (with optimized query support)
        from common_tasks.task_history import CeleryTaskHistory, TaskTypeFilter, OptimizedTaskHistoryQuery

        # Get Redis URL from environment
        redis_url = os.getenv("REDIS_RESULT_BACKEND", "redis://localhost:6379/1")

        # Use optimized query handler for better performance (SC-010: <1 second for 100+ tasks)
        optimized_query = OptimizedTaskHistoryQuery(redis_url)
        history = CeleryTaskHistory(redis_url)

        # Apply filtering if requested
        if task_type or state:
            filter_handler = TaskTypeFilter(redis_url)

            if task_type and state:
                # Filter by both type and state
                type_filtered = filter_handler.get_tasks_by_type(task_type)
                task_list = [t for t in type_filtered if t.get("status") == state]
            elif task_type:
                # Filter by type only
                task_list = filter_handler.get_tasks_by_type(task_type)
            else:
                # Filter by state only
                task_list = filter_handler.get_tasks_by_status(state)

            # Convert to task entries
            tasks = []
            for task_meta in task_list:
                task_entry = TaskHistoryEntry(
                    task_id=task_meta.get("task_id", ""),
                    task_type=task_meta.get("name", None),
                    state=task_meta.get("status", "UNKNOWN"),
                    submitted_at=None,
                    completed_at=datetime.fromtimestamp(task_meta.get("date_done", 0)) if task_meta.get("date_done") else None,
                    result_summary=str(task_meta.get("result", ""))[:100] if task_meta.get("result") else None
                )
                tasks.append(task_entry)
        else:
            # Scan all tasks using optimized pipeline queries
            # First, scan for task IDs
            task_ids = []
            for task_meta in history.scan_all_tasks_paginated(page_size=100):
                task_ids.append(task_meta.get("task_id", ""))

            # Then fetch full task data using Redis pipelines for better performance
            if task_ids:
                batch_results = optimized_query.get_tasks_batch_redis(task_ids)
                tasks = []
                for task_id, task_meta in batch_results.items():
                    task_entry = TaskHistoryEntry(
                        task_id=task_id,
                        task_type=task_meta.get("name", None),
                        state=task_meta.get("status", "UNKNOWN"),
                        submitted_at=None,
                        completed_at=datetime.fromtimestamp(task_meta.get("date_done", 0)) if task_meta.get("date_done") else None,
                        result_summary=str(task_meta.get("result", ""))[:100] if task_meta.get("result") else None
                    )
                    tasks.append(task_entry)
            else:
                tasks = []

        # Apply offset and limit
        total_count = len(tasks)
        tasks = tasks[offset:offset + limit]

        response = TaskHistoryResponse(
            tasks=tasks,
            total_count=total_count,
            timestamp=datetime.utcnow()
        )

        logger.info(
            f"Task history queried",
            extra={
                "total_count": total_count,
                "returned": len(tasks),
                "task_type_filter": task_type,
                "state_filter": state
            }
        )

        return response

    except ImportError as e:
        logger.error(f"Task history module not available: {e}")
        raise HTTPException(
            status_code=500,
            detail="Task history feature not available"
        )
    except Exception as e:
        logger.error(f"Error querying task history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error querying task history: {str(e)}"
        )
