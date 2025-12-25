"""
Worker Main Entry Point

Starts the Celery worker with configured settings.
"""

import logging
import os
import sys

# Add common module to path for local development
common_path = os.path.join(os.path.dirname(__file__), "../../../common/src")
if os.path.exists(common_path) and common_path not in sys.path:
    sys.path.insert(0, common_path)

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import Celery app and tasks AFTER configuring logging
try:
    from common_tasks.celery_app import celery_app
    # Import tasks to register them with the worker
    from common_tasks import tasks  # noqa: F401
except ImportError as e:
    logger.error(f"Failed to import common_tasks: {e}")
    logger.error(
        "Make sure the common module is installed. "
        "In Docker, run: pip install -e /app/common. "
        "For local dev, ensure common/src is in PYTHONPATH."
    )
    sys.exit(1)

from .config import get_worker_config


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