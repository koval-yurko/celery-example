"""
Notification Handlers for Example Service 2

Business logic for processing notifications.
Can be called either from Celery tasks or direct API requests.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from common_tasks.schemas import NotificationPayload, NotificationType
from common_tasks.tasks import send_notification
from common_tasks.celery_app import celery_app
from . import models

logger = logging.getLogger(__name__)


class NotificationHandler:
    """Handler for notification operations"""

    def send_notification_direct(
        self,
        recipient: str,
        notification_type: str,
        message: str,
        subject: str = None,
        metadata: dict = None,
    ) -> Dict:
        """
        Send a notification directly (not via task queue).

        This demonstrates that service-2 can operate independently,
        either consuming tasks OR receiving direct API calls.

        Args:
            recipient: Notification recipient
            notification_type: Type of notification (EMAIL, SMS, PUSH)
            message: Message content
            subject: Email subject (optional)
            metadata: Additional metadata (optional)

        Returns:
            dict: Delivery result
        """
        try:
            notification_id = f"NOTIF-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"

            # Validate notification type
            try:
                notif_type = NotificationType[notification_type.upper()]
            except KeyError:
                raise ValueError(f"Invalid notification type: {notification_type}")

            logger.info(f"Processing direct notification {notification_id}: {notif_type} to {recipient}")

            # Placeholder notification logic
            # In real implementation: integrate with external providers
            if notif_type == NotificationType.EMAIL:
                logger.info(f"[EMAIL] To: {recipient}, Subject: {subject}")
                logger.info(f"[EMAIL] Body: {message[:100]}...")
            elif notif_type == NotificationType.SMS:
                logger.info(f"[SMS] To: {recipient}")
                logger.info(f"[SMS] Message: {message[:100]}...")
            elif notif_type == NotificationType.PUSH:
                logger.info(f"[PUSH] To: {recipient}")
                logger.info(f"[PUSH] Message: {message[:100]}...")

            result = {
                "status": "sent",
                "notification_id": notification_id,
                "recipient": recipient,
                "notification_type": notification_type,
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "delivery_id": f"msg_{notification_id}",
            }

            logger.info(f"Notification {notification_id} sent successfully")
            return result

        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            raise

    def process_notification_from_task(self, payload: Dict) -> Dict:
        """
        Process a notification from a Celery task payload.

        This would be called by a Celery worker if service-2 runs workers.
        In the POC, the dedicated worker service handles task execution.

        Args:
            payload: NotificationPayload dict

        Returns:
            dict: Processing result
        """
        try:
            # Validate payload
            notif_data = NotificationPayload(**payload)

            logger.info(
                f"Processing notification task {notif_data.notification_id}: "
                f"{notif_data.notification_type} to {notif_data.recipient}"
            )

            # Use the same notification logic
            return self.send_notification_direct(
                recipient=notif_data.recipient,
                notification_type=notif_data.notification_type.value,
                message=notif_data.message,
                subject=notif_data.subject,
                metadata=notif_data.metadata,
            )

        except Exception as e:
            logger.error(f"Failed to process notification task: {str(e)}")
            raise


# Singleton instance
_handler_instance = None


def get_notification_handler() -> NotificationHandler:
    """Get or create the notification handler singleton"""
    global _handler_instance
    if _handler_instance is None:
        _handler_instance = NotificationHandler()
    return _handler_instance


# Task Submission Handlers for Service Endpoints Feature

def submit_multiply_task(x: float, y: float) -> Dict[str, Any]:
    """
    Submit a multiplication task to the Celery queue.

    Args:
        x: First operand
        y: Second operand

    Returns:
        dict: Task submission result with task_id and metadata
    """
    logger.info(f"Submitting multiply task: {x} * {y}")

    result = celery_app.send_task("multiply", args=[x, y], queue="default")

    logger.info(f"Multiply task submitted successfully. Task ID: {result.id}")

    return {
        "task_id": result.id,
        "task_type": "multiply",
        "status": "submitted",
        "submitted_at": datetime.now(timezone.utc),
    }


def submit_progress_task(iterations: int) -> Dict[str, Any]:
    """
    Submit a progress-tracked task to the Celery queue.

    Args:
        iterations: Number of iterations

    Returns:
        dict: Task submission result with task_id and metadata
    """
    logger.info(f"Submitting progress task with iterations={iterations}")

    result = celery_app.send_task("task_with_progress", args=[iterations], queue="default")

    logger.info(f"Progress task submitted successfully. Task ID: {result.id}")

    return {
        "task_id": result.id,
        "task_type": "task_with_progress",
        "status": "submitted",
        "submitted_at": datetime.now(timezone.utc),
    }


def submit_configurable_task(duration: int, should_succeed: bool) -> Dict[str, Any]:
    """
    Submit a configurable outcome task to the Celery queue.

    Args:
        duration: Duration in seconds
        should_succeed: Whether the task should succeed or fail

    Returns:
        dict: Task submission result with task_id and metadata
    """
    logger.info(f"Submitting configurable task: duration={duration}s, should_succeed={should_succeed}")

    result = celery_app.send_task("configurable_outcome_task", args=[duration, should_succeed], queue="default")

    logger.info(f"Configurable task submitted successfully. Task ID: {result.id}")

    return {
        "task_id": result.id,
        "task_type": "configurable_outcome_task",
        "status": "submitted",
        "submitted_at": datetime.now(timezone.utc),
    }


# NOTE: Task query handlers (get_task_status, get_task_result, get_task_history)
# have been moved to the API Gateway to avoid duplication.
# These functions are now implemented in api-gateway/src/api_gateway/handlers.py