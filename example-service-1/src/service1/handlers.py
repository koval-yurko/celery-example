"""
Task Handlers for Example Service 1

Business logic for publishing tasks to Celery queues.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict

from common_tasks.schemas import OrderPayload, OrderPriority
from common_tasks.tasks import process_order

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
            timestamp=datetime.utcnow(),
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
            "submitted_at": datetime.utcnow().isoformat(),
        }

    except ValueError as e:
        logger.error(f"Validation error for order {order_id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to submit order task for {order_id}: {str(e)}")
        raise Exception(f"Task submission failed: {str(e)}")