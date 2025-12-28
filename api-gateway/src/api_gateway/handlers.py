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
        timeout: Optional timeout in seconds (default: don't wait, return current state)

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


def get_task_history(limit: int = 100, offset: int = 0) -> TaskHistoryResponse:
    """
    Get task history from Redis result backend.

    This function uses direct Redis SCAN because Celery doesn't provide
    a native API for enumerating all tasks (by design, to remain backend-agnostic).

    Args:
        limit: Maximum number of tasks to return
        offset: Number of tasks to skip

    Returns:
        TaskHistoryResponse with list of all tasks

    Raises:
        HTTPException: 500 if query fails
    """
    try:
        # Import task history module from common_tasks
        from common_tasks.task_history import CeleryTaskHistory

        # Get Redis URL from environment
        redis_url = os.getenv("REDIS_RESULT_BACKEND", "redis://localhost:6379/1")

        # Create task history instance
        history = CeleryTaskHistory(redis_url)

        # Scan all tasks
        tasks = []
        for task_meta in history.scan_all_tasks_paginated(batch_size=100):
            task_entry = TaskHistoryEntry(
                task_id=task_meta.get("task_id", ""),
                task_type=task_meta.get("name", None),
                state=task_meta.get("status", "UNKNOWN"),
                submitted_at=None,  # Would need to be stored in task result
                completed_at=datetime.fromtimestamp(task_meta.get("date_done", 0)) if task_meta.get("date_done") else None,
                result_summary=str(task_meta.get("result", ""))[:100] if task_meta.get("result") else None
            )
            tasks.append(task_entry)

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
            extra={"total_count": total_count, "returned": len(tasks)}
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
