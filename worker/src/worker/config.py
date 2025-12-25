"""
Worker Configuration

Celery worker configuration with settings for reliability and performance.
"""

import os
import logging

logger = logging.getLogger(__name__)


class WorkerConfig:
    """Worker configuration settings"""

    def __init__(self):
        # Worker identity
        self.worker_name = os.getenv("WORKER_NAME", "celery-worker")

        # Concurrency settings
        self.concurrency = int(os.getenv("WORKER_CONCURRENCY", "2"))
        self.prefetch_multiplier = int(os.getenv("WORKER_PREFETCH_MULTIPLIER", "4"))
        self.max_tasks_per_child = int(os.getenv("WORKER_MAX_TASKS_PER_CHILD", "100"))

        # Queue configuration
        queues_str = os.getenv("WORKER_QUEUES", "orders,notifications,default")
        self.queues = [q.strip() for q in queues_str.split(",") if q.strip()]

        # Task configuration
        self.acks_late = os.getenv("CELERY_ACKS_LATE", "true").lower() == "true"
        self.task_reject_on_worker_lost = (
            os.getenv("CELERY_TASK_REJECT_ON_WORKER_LOST", "true").lower() == "true"
        )

        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    def log_config(self):
        """Log current configuration"""
        logger.info("Worker Configuration:")
        logger.info(f"  Worker Name: {self.worker_name}")
        logger.info(f"  Concurrency: {self.concurrency}")
        logger.info(f"  Prefetch Multiplier: {self.prefetch_multiplier}")
        logger.info(f"  Max Tasks Per Child: {self.max_tasks_per_child}")
        logger.info(f"  Queues: {', '.join(self.queues)}")
        logger.info(f"  Acks Late: {self.acks_late}")
        logger.info(f"  Reject on Worker Lost: {self.task_reject_on_worker_lost}")
        logger.info(f"  Log Level: {self.log_level}")

    def to_celery_args(self) -> list:
        """
        Convert configuration to Celery worker command-line arguments.

        Returns:
            list: Command-line arguments for Celery worker
        """
        args = []

        # Worker name
        args.extend(["-n", f"{self.worker_name}@%h"])

        # Concurrency
        args.extend(["--concurrency", str(self.concurrency)])

        # Prefetch
        args.extend(["--prefetch-multiplier", str(self.prefetch_multiplier)])

        # Max tasks per child (worker restart after N tasks)
        args.extend(["--max-tasks-per-child", str(self.max_tasks_per_child)])

        # Queues
        if self.queues:
            args.extend(["-Q", ",".join(self.queues)])

        # Log level
        args.extend(["--loglevel", self.log_level])

        return args


def get_worker_config() -> WorkerConfig:
    """Get worker configuration instance"""
    return WorkerConfig()