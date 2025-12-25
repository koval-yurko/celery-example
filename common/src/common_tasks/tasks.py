"""
Shared Task Definitions

Centralized task definitions used by all microservices and workers.
"""

import logging
from datetime import datetime
from typing import Dict

from .celery_app import celery_app
from .schemas import OrderPayload, NotificationPayload

logger = logging.getLogger(__name__)


@celery_app.task(
    name="tasks.process_order",
    queue="orders",
    max_retries=3,
    default_retry_delay=60,
)
def process_order(payload: Dict) -> Dict:
    """
    Process a customer order.

    This is a placeholder implementation. In a real system, this would:
    - Validate inventory
    - Reserve stock
    - Calculate shipping
    - Create payment transaction
    - Trigger notification

    Args:
        payload: OrderPayload serialized to dict

    Returns:
        dict: Processing result with status and order_id
    """
    try:
        # Validate payload
        order_data = OrderPayload(**payload)

        logger.info(f"Processing order {order_data.order_id} for customer {order_data.customer_id}")
        logger.info(f"Order contains {len(order_data.items)} items, total: ${order_data.total_amount}")

        # Placeholder processing logic
        # In real implementation: inventory check, payment processing, etc.

        # Simulate order processing
        result = {
            "status": "success",
            "order_id": order_data.order_id,
            "processed_at": datetime.utcnow().isoformat(),
            "message": f"Order {order_data.order_id} processed successfully",
        }

        logger.info(f"Order {order_data.order_id} processed successfully")
        return result

    except Exception as e:
        logger.error(f"Error processing order: {str(e)}")
        # In production, distinguish between retryable and non-retryable errors
        raise


@celery_app.task(
    name="tasks.send_notification",
    queue="notifications",
    max_retries=5,
    default_retry_delay=30,
)
def send_notification(payload: Dict) -> Dict:
    """
    Send notification to recipient.

    This is a placeholder implementation. In a real system, this would:
    - Integrate with email provider (SendGrid, SES, etc.)
    - Integrate with SMS provider (Twilio, etc.)
    - Integrate with push notification service (FCM, SNS, etc.)

    Args:
        payload: NotificationPayload serialized to dict

    Returns:
        dict: Delivery result with status and notification_id
    """
    try:
        # Validate payload
        notif_data = NotificationPayload(**payload)

        logger.info(
            f"Sending {notif_data.notification_type} notification {notif_data.notification_id} to {notif_data.recipient}"
        )

        # Placeholder notification logic
        # In real implementation: integrate with external notification providers

        result = {
            "status": "sent",
            "notification_id": notif_data.notification_id,
            "sent_at": datetime.utcnow().isoformat(),
            "delivery_id": f"msg_{notif_data.notification_id}",
        }

        logger.info(f"Notification {notif_data.notification_id} sent successfully")
        return result

    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        raise


@celery_app.task(
    name="tasks.health_check",
    queue="default",
)
def health_check() -> Dict:
    """
    Health check task to verify worker connectivity and queue availability.

    Returns:
        dict: Health status with timestamp and worker info
    """
    import socket

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "worker_id": f"{socket.gethostname()}",
    }