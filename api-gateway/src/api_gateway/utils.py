from typing import Optional, List, Dict, Any
from datetime import datetime, timezone


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


def parse_date_done(date_done) -> Optional[datetime]:
    """
    Parse date_done field which can be ISO string or numeric timestamp.

    Args:
        date_done: ISO format string, numeric timestamp, or None

    Returns:
        datetime object or None
    """
    if not date_done:
        return None

    if isinstance(date_done, (int, float)):
        return datetime.fromtimestamp(date_done)

    if isinstance(date_done, str):
        try:
            # Try ISO format first
            return datetime.fromisoformat(date_done.replace("Z", "+00:00"))
        except ValueError:
            try:
                # Try as numeric string
                return datetime.fromtimestamp(float(date_done))
            except ValueError:
                return None

    return None


def build_task_entry(task_id: Optional[str], task_meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a task entry dict from task metadata.

    Args:
        task_id: Task ID
        task_meta: Task metadata from Redis

    Returns:
        Dict with task entry fields
    """
    return {
        "task_id": task_id or task_meta.get("task_id", ""),
        "task_type": task_meta.get("name"),
        "state": task_meta.get("status", "UNKNOWN"),
        "submitted_at": None,
        "completed_at": parse_date_done(task_meta.get("date_done")),
        "result_summary": _truncate_result(task_meta.get("result")),
    }


def _truncate_result(result: Any) -> Optional[str]:
    """Truncate result to 100 chars for summary."""
    if not result:
        return None
    return str(result)[:100]


def get_filtered_task_list(filter_handler, task_type: Optional[str], state: Optional[str]) -> List[Dict]:
    """
    Get filtered task list based on type and/or state.

    Args:
        filter_handler: TaskTypeFilter instance
        task_type: Optional task type filter
        state: Optional state filter

    Returns:
        List of task metadata dicts
    """
    if task_type and state:
        type_filtered = filter_handler.get_tasks_by_type(task_type)
        return [t for t in type_filtered if t.get("status") == state]
    elif task_type:
        return filter_handler.get_tasks_by_type(task_type)
    else:
        return filter_handler.get_tasks_by_status(state)


def scan_all_task_ids(history) -> List[str]:
    """
    Scan all task IDs from Redis using pagination.

    Args:
        history: CeleryTaskHistory instance

    Returns:
        List of all task IDs
    """
    task_ids = []
    for page in history.scan_all_tasks_paginated(page_size=100):
        task_ids.extend(page.get("task_ids", []))
    return task_ids
