"""Celery application configuration."""
import os
from pathlib import Path
from celery import Celery
from dotenv import load_dotenv

# Load environment variables from .env file in project root
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

# Get Redis URL from environment
redis_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Create Celery app
app = Celery(
    'celery_example',
    broker=redis_url,
    backend=result_backend,
    include=['celery_example.tasks']  # Import tasks module
)

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

def main():
    """Entry point for celery-worker script."""
    app.worker_main(['worker', '--loglevel=info'])


if __name__ == '__main__':
    main()