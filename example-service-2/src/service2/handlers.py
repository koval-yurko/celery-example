"""
Notification Handlers for Example Service 2

Business logic for processing notifications.
Can be called either from Celery tasks or direct API requests.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict

from common_tasks.schemas import NotificationPayload, NotificationType

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
            notification_id = f"NOTIF-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"

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
                "sent_at": datetime.utcnow().isoformat(),
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