"""
API Endpoints for Example Service 1

RESTful API for submitting orders and checking health.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Dict
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .handlers import (
    submit_order_task,
    submit_add_task,
    submit_long_running_task,
    submit_process_data_task,
)
from .models import (
    AddTaskRequest,
    LongRunningTaskRequest,
    ProcessDataRequest,
    TaskSubmissionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class OrderRequest(BaseModel):
    """Order submission request"""

    order_id: str = Field(..., description="Unique order identifier")
    customer_id: str = Field(..., description="Customer ID")
    items: list[dict] = Field(..., description="Order line items")
    total_amount: float = Field(..., gt=0, description="Total order amount")
    priority: str = Field(default="NORMAL", description="Order priority: LOW, NORMAL, HIGH")


class OrderResponse(BaseModel):
    """Order submission response"""

    status: str = Field(..., description="Submission status")
    order_id: str = Field(..., description="Order ID")
    task_id: str = Field(..., description="Celery task ID")
    message: str = Field(..., description="Status message")


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    service: str
    timestamp: str
    redis_configured: bool


# Health Check Endpoint
@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint to verify service is running.

    Returns:
        HealthResponse with service status
    """
    redis_url = os.getenv("REDIS_BROKER_URL", "")
    return HealthResponse(
        status="healthy",
        service="example-service-1",
        timestamp=datetime.now(timezone.utc).isoformat(),
        redis_configured=bool(redis_url),
    )


# Order Submission Endpoint
@router.post("/api/orders", response_model=OrderResponse, status_code=202)
async def create_order(order: OrderRequest) -> OrderResponse:
    """
    Submit a new order for processing.

    This endpoint publishes the order to the Celery task queue for asynchronous processing.

    Args:
        order: Order details

    Returns:
        OrderResponse with task ID for tracking

    Raises:
        HTTPException: If order submission fails
    """
    try:
        logger.info(f"Received order submission request: {order.order_id}")

        # Submit order to task queue via handler
        task_result = submit_order_task(
            order_id=order.order_id,
            customer_id=order.customer_id,
            items=order.items,
            total_amount=order.total_amount,
            priority=order.priority,
        )

        logger.info(f"Order {order.order_id} submitted successfully. Task ID: {task_result['task_id']}")

        return OrderResponse(
            status="accepted",
            order_id=order.order_id,
            task_id=task_result["task_id"],
            message=f"Order {order.order_id} accepted for processing",
        )

    except ValueError as e:
        logger.error(f"Validation error for order {order.order_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting order {order.order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit order: {str(e)}")


# Order Status Endpoint (Optional - for demonstration)
@router.get("/api/orders/{order_id}", response_model=Dict)
async def get_order_status(order_id: str) -> Dict:
    """
    Get order processing status (placeholder).

    In a real system, this would query a database or result backend.

    Args:
        order_id: Order identifier

    Returns:
        Order status information
    """
    logger.info(f"Order status check requested for: {order_id}")

    # Placeholder response
    return {
        "order_id": order_id,
        "status": "processing",
        "message": "This is a placeholder. In production, this would query the result backend.",
    }


# Task Submission Endpoints

@router.post("/api/tasks/add", response_model=TaskSubmissionResponse, status_code=202)
async def submit_add(request: AddTaskRequest) -> TaskSubmissionResponse:
    """
    Submit an addition task to the Celery queue.

    This endpoint publishes an addition task for asynchronous processing.

    Args:
        request: Addition task parameters (x, y)

    Returns:
        TaskSubmissionResponse with task ID for tracking

    Raises:
        HTTPException: If task submission fails
    """
    try:
        logger.info(f"Received add task request: {request.x} + {request.y}")

        # Submit task via handler
        task_result = submit_add_task(x=request.x, y=request.y)

        logger.info(f"Add task submitted successfully. Task ID: {task_result['task_id']}")

        return TaskSubmissionResponse(
            status="accepted",
            task_id=task_result["task_id"],
            task_type=task_result["task_type"],
            submitted_at=task_result["submitted_at"],
            message="Addition task accepted for processing",
        )

    except ValueError as e:
        logger.error(f"Validation error for add task: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting add task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")


@router.post("/api/tasks/long-running", response_model=TaskSubmissionResponse, status_code=202)
async def submit_long_running(request: LongRunningTaskRequest) -> TaskSubmissionResponse:
    """
    Submit a long-running task to the Celery queue.

    This endpoint publishes a long-running task for asynchronous processing.

    Args:
        request: Long-running task parameters (duration)

    Returns:
        TaskSubmissionResponse with task ID for tracking

    Raises:
        HTTPException: If task submission fails
    """
    try:
        logger.info(f"Received long-running task request: duration={request.duration}s")

        # Submit task via handler
        task_result = submit_long_running_task(duration=request.duration)

        logger.info(f"Long-running task submitted successfully. Task ID: {task_result['task_id']}")

        return TaskSubmissionResponse(
            status="accepted",
            task_id=task_result["task_id"],
            task_type=task_result["task_type"],
            submitted_at=task_result["submitted_at"],
            message="Long-running task accepted for processing",
        )

    except ValueError as e:
        logger.error(f"Validation error for long-running task: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting long-running task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")


@router.post("/api/tasks/process-data", response_model=TaskSubmissionResponse, status_code=202)
async def submit_process_data(request: ProcessDataRequest) -> TaskSubmissionResponse:
    """
    Submit a data processing task to the Celery queue.

    This endpoint publishes a data processing task for asynchronous processing.

    Args:
        request: Data processing task parameters (data)

    Returns:
        TaskSubmissionResponse with task ID for tracking

    Raises:
        HTTPException: If task submission fails
    """
    try:
        logger.info("Received process-data task request")

        # Submit task via handler
        task_result = submit_process_data_task(data=request.data)

        logger.info(f"Process-data task submitted successfully. Task ID: {task_result['task_id']}")

        return TaskSubmissionResponse(
            status="accepted",
            task_id=task_result["task_id"],
            task_type=task_result["task_type"],
            submitted_at=task_result["submitted_at"],
            message="Data processing task accepted for processing",
        )

    except ValueError as e:
        logger.error(f"Validation error for process-data task: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting process-data task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")

