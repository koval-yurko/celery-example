"""
Celery Application Configuration

Centralized Celery configuration for all microservices.
"""

import os
from celery import Celery

# Read configuration from environment variables
REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL", "redis://localhost:6379/0")
REDIS_RESULT_BACKEND = os.getenv("REDIS_RESULT_BACKEND", "redis://localhost:6379/1")

# Create Celery app instance
celery_app = Celery("microservices")

# Configure Celery
celery_app.conf.update(
    # Broker and backend
    broker_url=REDIS_BROKER_URL,
    result_backend=REDIS_RESULT_BACKEND,

    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task routing
    task_routes={
        "tasks.process_order": {"queue": "orders"},
        "tasks.send_notification": {"queue": "notifications"},
        "tasks.health_check": {"queue": "default"},
    },

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour

    # Task execution settings
    task_acks_late=True,  # Acknowledge tasks after execution (for crash resilience)
    task_reject_on_worker_lost=True,  # Re-queue tasks if worker crashes

    # Worker settings (can be overridden by worker configuration)
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)