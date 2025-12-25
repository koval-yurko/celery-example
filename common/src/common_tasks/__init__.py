"""
Common Tasks Module

Shared task definitions and utilities for Celery microservices.
"""

__version__ = "0.1.0"

from .celery_app import celery_app
from .tasks import health_check, process_order, send_notification
from .schemas import TaskPayload, OrderPayload, NotificationPayload

__all__ = [
    "celery_app",
    "health_check",
    "process_order",
    "send_notification",
    "TaskPayload",
    "OrderPayload",
    "NotificationPayload",
]