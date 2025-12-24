"""Example script demonstrating Celery task execution."""
from celery_example.tasks import add, multiply, long_running_task, task_with_progress, process_data


def main():
    print("Celery Example - Submitting tasks to Redis queue")
    print("=" * 50)

    # Example 1: Simple synchronous task
    print("\n1. Simple add task (synchronous):")
    result = add.delay(4, 6)
    print(f"   Task ID: {result.id}")
    print(f"   Task state: {result.state}")
    print(f"   Waiting for result...")
    print(f"   Result: {result.get(timeout=10)}")

    # Example 2: Multiple tasks
    print("\n2. Multiple tasks:")
    task1 = add.delay(10, 20)
    task2 = multiply.delay(5, 8)
    print(f"   Add task: {task1.get()} (Task ID: {task1.id})")
    print(f"   Multiply task: {task2.get()} (Task ID: {task2.id})")

    # Example 3: Long-running task (async)
    print("\n3. Long-running task (5 seconds):")
    long_task = long_running_task.delay(5)
    print(f"   Task ID: {long_task.id}")
    print(f"   Task submitted! Not waiting for result.")
    print(f"   You can check status with: task.ready() = {long_task.ready()}")

    # Example 4: Process data
    print("\n4. Process data task:")
    data_task = process_data.delay({"name": "test", "value": 123})
    print(f"   Result: {data_task.get()}")

    # Example 5: Task with progress tracking
    print("\n5. Task with progress (20 iterations):")
    progress_task = task_with_progress.delay(20)
    while not progress_task.ready():
        if progress_task.state == 'PROGRESS':
            info = progress_task.info
            print(f"   Progress: {info.get('percent', 0)}%", end='\r')
    print(f"\n   Final result: {progress_task.get()}")

    print("\n" + "=" * 50)
    print("All tasks completed!")


if __name__ == "__main__":
    main()
