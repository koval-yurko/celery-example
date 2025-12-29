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

from common_tasks.celery_app import celery_app
from common_tasks.task_history import CeleryTaskHistory, TaskTypeFilter, OptimizedTaskHistoryQuery
from .utils import parse_date_done, utc_now, build_task_entry, get_filtered_task_list, scan_all_task_ids
from .models import TaskStatusResponse, TaskResultResponse, TaskHistoryResponse, TaskHistoryEntry

logger = logging.getLogger(__name__)

# Worker saturation threshold (configurable via environment variable)
MAX_ACTIVE_TASKS_PER_WORKER = int(os.getenv("MAX_ACTIVE_TASKS_PER_WORKER", "10"))

# Default timeout for AsyncResult.get() operations (configurable via environment variable)
DEFAULT_RESULT_TIMEOUT = float(os.getenv("CELERY_RESULT_TIMEOUT", "5.0"))


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
        tasks = _fetch_task_history(task_type, state)
        return _build_history_response(tasks, limit, offset, task_type, state)

    except ImportError as e:
        logger.error(f"Task history module not available: {e}")
        raise HTTPException(status_code=500, detail="Task history feature not available")
    except Exception as e:
        logger.error(f"Error querying task history: {e}")
        raise HTTPException(status_code=500, detail=f"Error querying task history: {str(e)}")


def _fetch_task_history(task_type: Optional[str], state: Optional[str]) -> list[TaskHistoryEntry]:
    """Fetch task history from Redis with optional filtering."""

    redis_url = os.getenv("REDIS_RESULT_BACKEND", "redis://localhost:6379/1")
    optimized_query = OptimizedTaskHistoryQuery(redis_url)
    history = CeleryTaskHistory(redis_url)

    if task_type or state:
        # fetch_filtered_tasks
        filter_handler = TaskTypeFilter(redis_url)
        task_list = get_filtered_task_list(filter_handler, task_type, state)

        return [
            TaskHistoryEntry(**build_task_entry(None, task_meta))
            for task_meta in task_list
        ]

    # fetch all task IDs
    task_ids = scan_all_task_ids(history)

    if not task_ids:
        return []

    batch_results = optimized_query.get_tasks_batch_redis(task_ids)
    return [
        TaskHistoryEntry(**build_task_entry(task_id, task_meta))
        for task_id, task_meta in batch_results.items()
    ]


def _build_history_response(
    tasks: list[TaskHistoryEntry],
    limit: int,
    offset: int,
    task_type: Optional[str],
    state: Optional[str]
) -> TaskHistoryResponse:
    """Build paginated history response."""
    total_count = len(tasks)
    paginated_tasks = tasks[offset:offset + limit]

    logger.info(
        "Task history queried",
        extra={
            "total_count": total_count,
            "returned": len(paginated_tasks),
            "task_type_filter": task_type,
            "state_filter": state
        }
    )

    return TaskHistoryResponse(
        tasks=paginated_tasks,
        total_count=total_count,
        timestamp=utc_now()
    )
