"""
Task Handlers for Example Service 1

Business logic for publishing tasks to Celery queues.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from common_tasks.schemas import OrderPayload, OrderPriority
from common_tasks.tasks import process_order
from common_tasks.celery_app import celery_app
from . import models

logger = logging.getLogger(__name__)


def submit_order_task(
    order_id: str,
    customer_id: str,
    items: list[dict],
    total_amount: float,
    priority: str = "NORMAL",
) -> Dict:
    """
    Submit an order processing task to the Celery queue.

    Args:
        order_id: Unique order identifier
        customer_id: Customer identifier
        items: List of order items
        total_amount: Total order amount
        priority: Order priority (LOW, NORMAL, HIGH)

    Returns:
        dict: Task submission result with task_id

    Raises:
        ValueError: If validation fails
        Exception: If task submission fails
    """
    try:
        # Generate unique task ID
        task_id = f"task-{uuid.uuid4().hex[:12]}"

        # Validate and create order payload
        order_payload = OrderPayload(
            task_id=task_id,
            timestamp=datetime.now(timezone.utc),
            source_service="example-service-1",
            order_id=order_id,
            customer_id=customer_id,
            items=items,
            total_amount=total_amount,
            priority=OrderPriority[priority.upper()],
        )

        logger.info(f"Publishing order task {task_id} for order {order_id}")
        logger.debug(f"Order payload: {order_payload.model_dump()}")

        # Submit task to Celery queue
        result = process_order.delay(order_payload.model_dump(mode="json"))

        logger.info(f"Task {task_id} submitted successfully. Celery task ID: {result.id}")

        return {
            "task_id": result.id,
            "order_id": order_id,
            "status": "submitted",
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }

    except ValueError as e:
        logger.error(f"Validation error for order {order_id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to submit order task for {order_id}: {str(e)}")
        raise Exception(f"Task submission failed: {str(e)}")


# Task Submission Handlers for Service Endpoints Feature

def submit_add_task(x: float, y: float) -> Dict[str, Any]:
    """
    Submit an addition task to the Celery queue.

    Args:
        x: First operand
        y: Second operand

    Returns:
        dict: Task submission result with task_id and metadata
    """
    logger.info(f"Submitting add task: {x} + {y}")

    result = celery_app.send_task("add", args=[x, y], queue="default")

    logger.info(f"Add task submitted successfully. Task ID: {result.id}")

    return {
        "task_id": result.id,
        "task_type": "add",
        "status": "submitted",
        "submitted_at": datetime.now(timezone.utc),
    }


def submit_long_running_task(duration: int) -> Dict[str, Any]:
    """
    Submit a long-running task to the Celery queue.

    Args:
        duration: Duration in seconds

    Returns:
        dict: Task submission result with task_id and metadata
    """
    logger.info(f"Submitting long-running task with duration={duration}s")

    result = celery_app.send_task("long_running_task", args=[duration], queue="default")

    logger.info(f"Long-running task submitted successfully. Task ID: {result.id}")

    return {
        "task_id": result.id,
        "task_type": "long_running_task",
        "status": "submitted",
        "submitted_at": datetime.now(timezone.utc),
    }


def submit_process_data_task(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Submit a data processing task to the Celery queue.

    Args:
        data: Data to process

    Returns:
        dict: Task submission result with task_id and metadata
    """
    logger.info("Submitting process_data task")

    result = celery_app.send_task("process_data", args=[data], queue="default")

    logger.info(f"Process data task submitted successfully. Task ID: {result.id}")

    return {
        "task_id": result.id,
        "task_type": "process_data",
        "status": "submitted",
        "submitted_at": datetime.now(timezone.utc),
    }


# NOTE: Task query handlers (get_task_status, get_task_result, get_task_history)
# have been moved to the API Gateway to avoid duplication.
# These functions are now implemented in api-gateway/src/api_gateway/handlers.py