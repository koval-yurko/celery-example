"""
API Endpoints for Example Service 2

RESTful API for notification management and health checks.
"""

import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .handlers import (
    get_notification_handler,
    submit_multiply_task,
    submit_progress_task,
    submit_configurable_task,
)
from .models import (
    MultiplyTaskRequest,
    ProgressTaskRequest,
    ConfigurableOutcomeTaskRequest,
    TaskSubmissionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class NotificationRequest(BaseModel):
    """Direct notification send request"""

    recipient: str = Field(..., description="Notification recipient")
    notification_type: str = Field(..., description="Type: EMAIL, SMS, PUSH")
    message: str = Field(..., description="Notification message content")
    subject: Optional[str] = Field(None, description="Email subject (optional)")


class NotificationResponse(BaseModel):
    """Notification send response"""

    status: str = Field(..., description="Delivery status")
    notification_id: str = Field(..., description="Notification ID")
    recipient: str = Field(..., description="Recipient")
    notification_type: str = Field(..., description="Notification type")
    sent_at: str = Field(..., description="Timestamp when sent")
    delivery_id: str = Field(..., description="External delivery ID")


class NotificationStatusResponse(BaseModel):
    """Notification status response"""

    notification_id: str
    status: str
    message: str


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
    return HealthResponse(
        status="healthy",
        service="example-service-2",
        timestamp=datetime.utcnow().isoformat(),
        redis_configured=bool(os.getenv("REDIS_BROKER_URL")),
    )


# Notification Status Endpoint
@router.get("/api/notifications/{notification_id}", response_model=NotificationStatusResponse)
async def get_notification(notification_id: str) -> NotificationStatusResponse:
    """
    Get notification status (placeholder).

    In a real system, this would query a database.

    Args:
        notification_id: Notification identifier

    Returns:
        Notification status information
    """
    logger.info(f"Notification status check for: {notification_id}")
    return NotificationStatusResponse(
        notification_id=notification_id,
        status="sent",
        message="This is a placeholder. In production, this would query a database.",
    )


# Direct Notification Send Endpoint
@router.post("/api/notifications/send", response_model=NotificationResponse)
async def send_notification_direct(request: NotificationRequest) -> NotificationResponse:
    """
    Direct notification send endpoint (alternative to task queue).

    This demonstrates that service-2 can operate independently,
    either consuming tasks from queue OR receiving direct API calls.

    Args:
        request: Notification details

    Returns:
        NotificationResponse with delivery status

    Raises:
        HTTPException: If notification send fails
    """
    try:
        logger.info(f"Direct notification send request: {request.notification_type} to {request.recipient}")

        result = get_notification_handler().send_notification_direct(
            recipient=request.recipient,
            notification_type=request.notification_type,
            message=request.message,
            subject=request.subject,
        )

        return NotificationResponse(**result)

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")


# Task Submission Endpoints

@router.post("/api/tasks/multiply", response_model=TaskSubmissionResponse, status_code=202)
async def submit_multiply(request: MultiplyTaskRequest) -> TaskSubmissionResponse:
    """
    Submit a multiplication task to the Celery queue.

    This endpoint publishes a multiplication task for asynchronous processing.

    Args:
        request: Multiplication task parameters (x, y)

    Returns:
        TaskSubmissionResponse with task ID for tracking

    Raises:
        HTTPException: If task submission fails
    """
    try:
        logger.info(f"Received multiply task request: {request.x} * {request.y}")

        # Submit task via handler
        task_result = submit_multiply_task(x=request.x, y=request.y)

        logger.info(f"Multiply task submitted successfully. Task ID: {task_result['task_id']}")

        return TaskSubmissionResponse(
            status="accepted",
            task_id=task_result["task_id"],
            task_type=task_result["task_type"],
            submitted_at=task_result["submitted_at"],
            message=f"Multiplication task accepted for processing",
        )

    except ValueError as e:
        logger.error(f"Validation error for multiply task: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting multiply task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")


@router.post("/api/tasks/progress", response_model=TaskSubmissionResponse, status_code=202)
async def submit_progress(request: ProgressTaskRequest) -> TaskSubmissionResponse:
    """
    Submit a progress-tracked task to the Celery queue.

    This endpoint publishes a progress-tracked task for asynchronous processing.

    Args:
        request: Progress task parameters (iterations)

    Returns:
        TaskSubmissionResponse with task ID for tracking

    Raises:
        HTTPException: If task submission fails
    """
    try:
        logger.info(f"Received progress task request: iterations={request.iterations}")

        # Submit task via handler
        task_result = submit_progress_task(iterations=request.iterations)

        logger.info(f"Progress task submitted successfully. Task ID: {task_result['task_id']}")

        return TaskSubmissionResponse(
            status="accepted",
            task_id=task_result["task_id"],
            task_type=task_result["task_type"],
            submitted_at=task_result["submitted_at"],
            message=f"Progress-tracked task accepted for processing",
        )

    except ValueError as e:
        logger.error(f"Validation error for progress task: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting progress task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")


@router.post("/api/tasks/configurable", response_model=TaskSubmissionResponse, status_code=202)
async def submit_configurable(request: ConfigurableOutcomeTaskRequest) -> TaskSubmissionResponse:
    """
    Submit a configurable outcome task to the Celery queue.

    This endpoint publishes a configurable outcome task for asynchronous processing.

    Args:
        request: Configurable task parameters (duration, should_succeed)

    Returns:
        TaskSubmissionResponse with task ID for tracking

    Raises:
        HTTPException: If task submission fails
    """
    try:
        logger.info(f"Received configurable task request: duration={request.duration}s, should_succeed={request.should_succeed}")

        # Submit task via handler
        task_result = submit_configurable_task(duration=request.duration, should_succeed=request.should_succeed)

        logger.info(f"Configurable task submitted successfully. Task ID: {task_result['task_id']}")

        return TaskSubmissionResponse(
            status="accepted",
            task_id=task_result["task_id"],
            task_type=task_result["task_type"],
            submitted_at=task_result["submitted_at"],
            message=f"Configurable outcome task accepted for processing",
        )

    except ValueError as e:
        logger.error(f"Validation error for configurable task: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting configurable task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")

