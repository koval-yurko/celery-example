"""
Worker Main Entry Point

Starts the Celery worker with configured settings.
"""

import logging
import os

from common_tasks import tasks  # noqa: F401
from common_tasks.celery_app import celery_app

from .config import get_worker_config

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def configure_celery_app():
    """Configure Celery application settings"""
    config = get_worker_config()

    # Update Celery configuration
    celery_app.conf.update(
        worker_prefetch_multiplier=config.prefetch_multiplier,
        task_acks_late=config.acks_late,
        task_reject_on_worker_lost=config.task_reject_on_worker_lost,
        # Additional reliability settings for POC
        worker_max_tasks_per_child=config.max_tasks_per_child,
    )

    logger.info("Celery app configured successfully")
    return celery_app


def main():
    """Main entry point for worker"""
    logger.info("=" * 60)
    logger.info("Starting Celery Worker")
    logger.info("=" * 60)

    # Get worker configuration
    config = get_worker_config()
    config.log_config()

    # Configure Celery app
    app = configure_celery_app()

    # Log registered tasks
    logger.info("Registered tasks:")
    for task_name in sorted(app.tasks.keys()):
        if not task_name.startswith("celery."):
            logger.info(f"  - {task_name}")

    logger.info("=" * 60)

    # Build worker command arguments
    worker_args = ["worker"] + config.to_celery_args()

    logger.info(f"Starting worker with args: {' '.join(worker_args)}")

    # Start the worker
    # Note: app.worker_main() runs the worker in-process
    app.worker_main(argv=worker_args)


if __name__ == "__main__":
    main()