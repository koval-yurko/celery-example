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

from .handlers import get_notification_handler

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