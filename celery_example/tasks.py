"""Example Celery tasks."""
import time
from celery_example.worker import app


@app.task
def add(x, y):
    """Add two numbers together."""
    return x + y


@app.task
def multiply(x, y):
    """Multiply two numbers."""
    return x * y


@app.task
def long_running_task(duration=10):
    """Simulate a long-running task.

    Args:
        duration: Time to sleep in seconds (default: 10)

    Returns:
        Success message with duration
    """
    print(f"Starting long task that will run for {duration} seconds...")
    time.sleep(duration)
    return f"Task completed after {duration} seconds"


@app.task(bind=True)
def task_with_progress(self, total=100):
    """Task that reports progress.

    Args:
        total: Total number of iterations (default: 100)

    Returns:
        Completion message
    """
    for i in range(total):
        # Update task state with progress
        self.update_state(
            state='PROGRESS',
            meta={'current': i, 'total': total, 'percent': int((i / total) * 100)}
        )
        time.sleep(0.1)  # Simulate work

    return {'current': total, 'total': total, 'percent': 100, 'status': 'Complete'}


@app.task
def process_data(data):
    """Process some data.

    Args:
        data: Dictionary with data to process

    Returns:
        Processed result
    """
    # Simulate data processing
    result = {
        'input': data,
        'processed': True,
        'timestamp': time.time()
    }
    return result
