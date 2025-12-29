"""
Celery Task History Query Module

Provides efficient patterns for querying task history from Redis result backend,
retrieving task metadata, and handling errors gracefully.

Usage:
    from common_tasks.task_history import CeleryTaskHistory, RobustTaskQueryHandler
    from common_tasks.celery_app import celery_app

    # Get all tasks paginated
    history = CeleryTaskHistory()
    for page in history.scan_all_tasks_paginated(page_size=50):
        print(f"Page {page['count']} tasks found")

    # Get specific task safely
    handler = RobustTaskQueryHandler(celery_app)
    info = handler.get_task_state_safely(task_id)
"""

import json
import logging
import redis
from typing import List, Dict, Generator, Optional, Any
from datetime import datetime, timedelta
from celery.result import AsyncResult
from celery import Celery
from celery.exceptions import TimeoutError as CeleryTimeoutError

logger = logging.getLogger(__name__)


class CeleryTaskHistory:
    """
    Efficiently query Celery task history from Redis result backend using SCAN.

    Uses cursor-based pagination (SCAN) instead of blocking KEYS operation.
    Suitable for querying 100+ tasks without blocking Redis.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/1", batch_size: int = 100):
        """
        Initialize task history query handler.

        Args:
            redis_url: Redis URL for result backend (default: database 1)
            batch_size: Number of keys per SCAN iteration (hint, not guaranteed)
        """
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.pattern = "celery-task-meta-*"
        self.batch_size = batch_size

    def get_all_task_ids(self, cursor: int = 0, count: int = None) -> Dict[str, Any]:
        """
        Scan Redis for task IDs using cursor-based pagination.

        Args:
            cursor: Starting cursor position (0 for first scan)
            count: Approximate keys per batch (COUNT is a hint, not guaranteed)

        Returns:
            {
                'task_ids': List[str],      # Cleaned task IDs
                'cursor': int,              # Next cursor for pagination
                'completed': bool,          # True when cursor == 0
                'count': int                # Number of task_ids in this batch
            }
        """
        if count is None:
            count = self.batch_size

        try:
            cursor, keys = self.redis_client.scan(
                cursor=cursor,
                match=self.pattern,
                count=count
            )

            # Extract task IDs: "celery-task-meta-<uuid>" -> "<uuid>"
            task_ids = [
                key.replace("celery-task-meta-", "") for key in keys
            ]

            return {
                "task_ids": task_ids,
                "cursor": cursor,
                "completed": cursor == 0,
                "count": len(task_ids)
            }

        except redis.ConnectionError as e:
            logger.error(f"Redis connection error during SCAN: {str(e)}")
            raise

    def scan_all_tasks_paginated(self, page_size: int = 100) -> Generator[Dict, None, None]:
        """
        Generator for iterating through all tasks with pagination.

        Usage:
            for page in history.scan_all_tasks_paginated(page_size=100):
                tasks = page['task_ids']  # List of task IDs
                print(f"Found {page['count']} tasks in this batch")
                if page['completed']:
                    break

        Args:
            page_size: Keys to request per SCAN iteration

        Yields:
            Dictionary with task_ids and pagination info
        """
        cursor = 0

        while True:
            result = self.get_all_task_ids(cursor=cursor, count=page_size)

            if result['task_ids']:
                yield result

            cursor = result['cursor']
            if result['completed']:
                break

    def get_task_metadata(self, task_id: str) -> Dict[str, Any]:
        """
        Retrieve complete task metadata from result backend.

        Args:
            task_id: Celery task UUID

        Returns:
            {
                'task_id': str,
                'state': str,              # PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED
                'result': Any,             # Task result if successful
                'error': Optional[str],    # Error message if failed
                'traceback': Optional[str],# Exception traceback
                'task_name': Optional[str],# Task name (requires extended metadata)
                'args': Optional[list],    # Task args (requires extended metadata)
                'kwargs': Optional[dict],  # Task kwargs (requires extended metadata)
                'worker': Optional[str],   # Worker name (requires extended metadata)
            }
        """
        result = AsyncResult(task_id)

        try:
            # Get raw metadata from backend
            info = result.info

            metadata = {
                "task_id": task_id,
                "state": result.state,
                "result": None,
                "error": None,
                "traceback": None,
                "task_name": None,
                "args": None,
                "kwargs": None,
                "worker": None,
            }

            # Handle different result types
            if isinstance(info, dict):
                # Extended metadata or state dict
                metadata["result"] = info.get('result')
                metadata["error"] = info.get('exc_message')
                metadata["traceback"] = info.get('traceback')
                metadata["task_name"] = info.get('name')
                metadata["args"] = info.get('args')
                metadata["kwargs"] = info.get('kwargs')
                metadata["worker"] = info.get('worker')

            elif isinstance(info, Exception):
                # Exception object
                metadata["error"] = str(info)
                metadata["traceback"] = result.traceback

            elif result.successful():
                # Result is the actual return value
                metadata["result"] = result.result

            return metadata

        except Exception as e:
            logger.warning(f"Error retrieving metadata for task {task_id}: {str(e)}")
            return {
                "task_id": task_id,
                "state": result.state,
                "error": f"Metadata retrieval failed: {str(e)}",
                "result": None,
                "traceback": None,
            }

    def get_multiple_task_metadata(self, task_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieve metadata for multiple tasks efficiently.

        Still more efficient than individual AsyncResult calls due to
        bulk resource cleanup.

        Args:
            task_ids: List of task UUIDs

        Returns:
            List of metadata dictionaries
        """
        metadata_list = []
        results = [AsyncResult(tid) for tid in task_ids]

        for result in results:
            try:
                info = result.info

                metadata = {
                    "task_id": result.id,
                    "state": result.state,
                    "result": None,
                    "error": None,
                }

                if isinstance(info, dict):
                    metadata["result"] = info.get('result')
                    metadata["error"] = info.get('exc_message')
                elif isinstance(info, Exception):
                    metadata["error"] = str(info)
                elif result.successful():
                    metadata["result"] = result.result

                metadata_list.append(metadata)

            except Exception as e:
                metadata_list.append({
                    "task_id": result.id,
                    "state": result.state,
                    "error": f"Failed to retrieve: {str(e)}"
                })

        return metadata_list


class OptimizedTaskHistoryQuery:
    """
    Query task states directly from Redis using pipelines for efficiency.

    More performant than AsyncResult for batch operations.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        """Initialize Redis client for direct queries."""
        self.redis = redis.from_url(redis_url, decode_responses=True)

    def get_tasks_batch_redis(self, task_ids: List[str]) -> Dict[str, Dict]:
        """
        Query multiple task states from Redis in a single pipeline operation.

        Much more efficient than individual AsyncResult calls.

        Args:
            task_ids: List of task UUIDs

        Returns:
            Dictionary mapping task_id to task state dict
        """
        if not task_ids:
            return {}

        pipeline = self.redis.pipeline()

        # Queue all GET commands
        for task_id in task_ids:
            key = f"celery-task-meta-{task_id}"
            pipeline.get(key)

        try:
            # Execute all at once (single round-trip to Redis)
            results = pipeline.execute()

            task_states = {}
            for task_id, raw_value in zip(task_ids, results):
                if raw_value:
                    try:
                        task_states[task_id] = json.loads(raw_value)
                    except json.JSONDecodeError:
                        task_states[task_id] = {"status": "CORRUPTED", "raw": raw_value}
                else:
                    task_states[task_id] = {"status": "PENDING"}

            return task_states

        except redis.ConnectionError as e:
            logger.error(f"Redis connection error during pipeline: {str(e)}")
            raise

    def paginate_task_history(
        self,
        page_size: int = 100,
        filter_state: Optional[str] = None,
        filter_task_name: Optional[str] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Efficiently paginate through task history with optional filtering.

        Args:
            page_size: Keys to scan per iteration
            filter_state: Only return tasks with this state (SUCCESS, FAILURE, etc.)
            filter_task_name: Only return tasks with this name

        Yields:
            {
                'page': int,
                'tasks': Dict[task_id -> state],
                'total_in_page': int,
                'has_more': bool
            }
        """
        cursor = 0
        page = 0

        while True:
            try:
                cursor, keys = self.redis.scan(
                    cursor=cursor,
                    match="celery-task-meta-*",
                    count=page_size
                )

                if not keys:
                    if cursor == 0:
                        break
                    continue

                # Extract task IDs
                task_ids = [k.replace("celery-task-meta-", "") for k in keys]

                # Batch query all states
                task_states = self.get_tasks_batch_redis(task_ids)

                # Apply filters
                if filter_state or filter_task_name:
                    filtered = {}
                    for tid, state in task_states.items():
                        if filter_state and state.get('status') != filter_state:
                            continue
                        if filter_task_name and state.get('name') != filter_task_name:
                            continue
                        filtered[tid] = state
                    task_states = filtered

                if task_states:
                    page += 1
                    yield {
                        "page": page,
                        "tasks": task_states,
                        "total_in_page": len(task_states),
                        "has_more": cursor != 0
                    }

                if cursor == 0:
                    break

            except redis.ConnectionError as e:
                logger.error(f"Redis connection error: {str(e)}")
                break


class RobustTaskQueryHandler:
    """
    Safe task state retrieval with comprehensive error handling.

    Handles all Celery task states and backend errors gracefully.
    """

    def __init__(self, celery_app: Celery, timeout: int = 5):
        """
        Initialize task query handler.

        Args:
            celery_app: Celery application instance
            timeout: Timeout for get() operations in seconds
        """
        self.app = celery_app
        self.timeout = timeout

    def get_task_state_safely(self, task_id: str) -> Dict[str, Any]:
        """
        Safely retrieve task state with comprehensive error handling.

        Handles all Celery states:
        - PENDING: Not yet executed
        - RECEIVED: Broker received message
        - STARTED: Execution started
        - SUCCESS: Completed successfully
        - FAILURE: Failed with exception
        - RETRY: Being retried
        - REVOKED: Manually revoked

        Args:
            task_id: Celery task UUID

        Returns:
            {
                'task_id': str,
                'status': str,       # PENDING, RUNNING, SUCCESS, FAILED, RETRYING, REVOKED, UNKNOWN
                'result': Any,       # Task result if successful
                'error': Optional[Dict],  # Error details if failed
            }
        """
        result = AsyncResult(task_id, app=self.app)

        try:
            state = result.state

            if state == 'PENDING':
                return {
                    'task_id': task_id,
                    'status': 'PENDING',
                    'result': None,
                    'error': None,
                }

            elif state == 'RECEIVED':
                return {
                    'task_id': task_id,
                    'status': 'RECEIVED',
                    'result': None,
                    'error': None,
                }

            elif state == 'STARTED':
                return {
                    'task_id': task_id,
                    'status': 'RUNNING',
                    'result': None,
                    'error': None,
                }

            elif state == 'SUCCESS':
                try:
                    task_result = result.get(timeout=self.timeout)
                    return {
                        'task_id': task_id,
                        'status': 'SUCCESS',
                        'result': task_result,
                        'error': None,
                    }
                except CeleryTimeoutError:
                    return {
                        'task_id': task_id,
                        'status': 'SUCCESS',
                        'result': None,
                        'error': {
                            'type': 'TimeoutError',
                            'message': f'Timeout retrieving result after {self.timeout}s'
                        }
                    }

            elif state == 'FAILURE':
                info = result.info
                return {
                    'task_id': task_id,
                    'status': 'FAILED',
                    'result': None,
                    'error': {
                        'type': type(info).__name__ if isinstance(info, Exception) else 'Unknown',
                        'message': str(info),
                        'traceback': result.traceback,
                    }
                }

            elif state == 'RETRY':
                info = result.info
                return {
                    'task_id': task_id,
                    'status': 'RETRYING',
                    'result': None,
                    'error': {
                        'type': 'RetryError',
                        'message': str(info) if info else 'Task being retried',
                    }
                }

            elif state == 'REVOKED':
                return {
                    'task_id': task_id,
                    'status': 'REVOKED',
                    'result': None,
                    'error': {
                        'type': 'RevokedError',
                        'message': 'Task was revoked/cancelled'
                    }
                }

            else:
                return {
                    'task_id': task_id,
                    'status': state,
                    'result': None,
                    'error': None,
                }

        except Exception as e:
            logger.error(f"Error querying task {task_id}: {str(e)}")
            return {
                'task_id': task_id,
                'status': 'UNKNOWN',
                'result': None,
                'error': {
                    'type': 'QueryError',
                    'message': f'Backend query failed: {str(e)}'
                }
            }


class TaskTypeFilter:
    """
    Filter and group tasks by type/name or other attributes.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        """Initialize with Redis connection."""
        self.redis = redis.from_url(redis_url, decode_responses=True)

    def get_tasks_by_type(self, task_name: str) -> List[Dict]:
        """
        Get all tasks of a specific type/name.

        Args:
            task_name: Task name (e.g., 'tasks.process_order')

        Returns:
            List of tasks matching the name
        """
        matching_tasks = []
        cursor = 0

        while True:
            cursor, keys = self.redis.scan(
                cursor=cursor,
                match="celery-task-meta-*"
            )

            for key in keys:
                task_data = self.redis.get(key)
                if task_data:
                    try:
                        metadata = json.loads(task_data)
                        if metadata.get('name') == task_name:
                            task_id = key.replace("celery-task-meta-", "")
                            matching_tasks.append({
                                'task_id': task_id,
                                'name': metadata.get('name'),
                                'status': metadata.get('status'),
                                'result': metadata.get('result'),
                            })
                    except json.JSONDecodeError:
                        pass

            if cursor == 0:
                break

        return matching_tasks

    def get_tasks_by_status(self, status: str) -> List[Dict]:
        """
        Get all tasks with a specific status.

        Args:
            status: Task status (PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED)

        Returns:
            List of tasks with the specified status
        """
        matching_tasks = []
        cursor = 0

        while True:
            cursor, keys = self.redis.scan(
                cursor=cursor,
                match="celery-task-meta-*"
            )

            for key in keys:
                task_data = self.redis.get(key)
                if task_data:
                    try:
                        metadata = json.loads(task_data)
                        if metadata.get('status') == status:
                            task_id = key.replace("celery-task-meta-", "")
                            matching_tasks.append({
                                'task_id': task_id,
                                'name': metadata.get('name'),
                                'status': status,
                            })
                    except json.JSONDecodeError:
                        pass

            if cursor == 0:
                break

        return matching_tasks

    def group_tasks_by_type(self) -> Dict[str, List]:
        """
        Group all tasks by their type/name.

        Returns:
            Dictionary mapping task names to lists of task info
        """
        grouped = {}
        cursor = 0

        while True:
            cursor, keys = self.redis.scan(
                cursor=cursor,
                match="celery-task-meta-*"
            )

            for key in keys:
                task_data = self.redis.get(key)
                if task_data:
                    try:
                        metadata = json.loads(task_data)
                        task_name = metadata.get('name', 'unknown')

                        if task_name not in grouped:
                            grouped[task_name] = []

                        task_id = key.replace("celery-task-meta-", "")
                        grouped[task_name].append({
                            'task_id': task_id,
                            'status': metadata.get('status'),
                        })
                    except json.JSONDecodeError:
                        pass

            if cursor == 0:
                break

        return grouped

    def get_task_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics about tasks in the backend.

        Returns:
            {
                'total_tasks': int,
                'by_status': Dict[status -> count],
                'by_type': Dict[type -> count]
            }
        """
        stats = {
            'total_tasks': 0,
            'by_status': {},
            'by_type': {}
        }
        cursor = 0

        while True:
            cursor, keys = self.redis.scan(
                cursor=cursor,
                match="celery-task-meta-*"
            )

            for key in keys:
                task_data = self.redis.get(key)
                if task_data:
                    try:
                        metadata = json.loads(task_data)

                        stats['total_tasks'] += 1

                        status = metadata.get('status', 'unknown')
                        stats['by_status'][status] = stats['by_status'].get(status, 0) + 1

                        task_type = metadata.get('name', 'unknown')
                        stats['by_type'][task_type] = stats['by_type'].get(task_type, 0) + 1

                    except json.JSONDecodeError:
                        pass

            if cursor == 0:
                break

        return stats
