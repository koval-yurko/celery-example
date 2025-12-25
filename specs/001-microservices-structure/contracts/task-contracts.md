# Task Contracts: Celery Task Signatures

**Feature**: 001-microservices-structure
**Date**: 2025-12-25
**Protocol**: Celery Task Queues

## Overview

This document defines the task contracts (Celery task signatures) used for inter-service communication. All tasks are defined in `common/src/common_tasks/tasks.py` and imported by services and workers.

---

## Task: process_order

**Purpose**: Process a customer order (published by example-service-1, executed by worker)

**Queue**: `orders` (dedicated queue for order processing tasks)

**Signature**:
```python
@celery_app.task(
    name='tasks.process_order',
    queue='orders',
    acks_late=True,
    max_retries=3,
    default_retry_delay=60
)
def process_order(payload: dict) -> dict:
    """
    Process a customer order.

    Args:
        payload (dict): OrderPayload serialized to dict
            - task_id (str): Unique task identifier
            - timestamp (str): ISO 8601 datetime
            - source_service (str): Originating service name
            - order_id (str): Unique order identifier
            - customer_id (str): Customer identifier
            - items (list[dict]): Order line items
            - total_amount (float): Total order value
            - priority (str, optional): Order priority (LOW, NORMAL, HIGH)

    Returns:
        dict: Processing result
            - status (str): "success" or "failed"
            - order_id (str): Processed order ID
            - processed_at (str): ISO 8601 datetime
            - notification_task_id (str, optional): Triggered notification task ID

    Raises:
        ValidationError: If payload doesn't match OrderPayload schema
        ProcessingError: If order processing fails (will retry)
    """
```

**Request Example**:
```python
from common_tasks.tasks import process_order
from common_tasks.schemas import OrderPayload

payload = OrderPayload(
    task_id="task-001",
    timestamp="2025-12-25T10:00:00Z",
    source_service="example-service-1",
    order_id="ORD-20251225-abc123",
    customer_id="CUST-456",
    items=[
        {"product_id": "PROD-789", "quantity": 2}
    ],
    total_amount=99.98,
    priority="NORMAL"
)

# Async execution
result = process_order.delay(payload.model_dump())

# Get result (if needed)
# result.get(timeout=300)  # Wait up to 5 minutes
```

**Response Example** (success):
```json
{
    "status": "success",
    "order_id": "ORD-20251225-abc123",
    "processed_at": "2025-12-25T10:01:30Z",
    "notification_task_id": "task-002"
}
```

**Response Example** (failure):
```json
{
    "status": "failed",
    "order_id": "ORD-20251225-abc123",
    "error": "Inventory unavailable",
    "retry_count": 2
}
```

**Error Handling**:
- **ValidationError**: Immediate failure, no retry (invalid payload)
- **TransientError** (network, timeout): Retry up to 3 times with 60s delay
- **PermanentError** (business logic failure): Fail immediately, no retry

**Retry Policy**:
- Max retries: 3
- Retry delay: 60 seconds (linear, not exponential in POC)
- Retry on: Connection errors, timeout errors
- No retry on: Validation errors, business logic errors

**Performance**:
- Expected execution time: 1-5 seconds
- Timeout: 300 seconds (5 minutes)
- Priority queue support: HIGH priority tasks jump queue

---

## Task: send_notification

**Purpose**: Send notification to customer (published by worker, executed by example-service-2 or worker)

**Queue**: `notifications` (dedicated queue for notification tasks)

**Signature**:
```python
@celery_app.task(
    name='tasks.send_notification',
    queue='notifications',
    acks_late=True,
    max_retries=5,
    default_retry_delay=30
)
def send_notification(payload: dict) -> dict:
    """
    Send notification to recipient.

    Args:
        payload (dict): NotificationPayload serialized to dict
            - task_id (str): Unique task identifier
            - timestamp (str): ISO 8601 datetime
            - source_service (str): Originating service name
            - notification_id (str): Unique notification identifier
            - recipient (str): Notification recipient
            - notification_type (str): EMAIL, SMS, or PUSH
            - subject (str, optional): Notification subject (EMAIL only)
            - message (str): Notification message content
            - metadata (dict, optional): Additional context

    Returns:
        dict: Delivery result
            - status (str): "sent", "failed", or "queued"
            - notification_id (str): Processed notification ID
            - sent_at (str): ISO 8601 datetime
            - delivery_id (str, optional): External provider delivery ID

    Raises:
        ValidationError: If payload doesn't match NotificationPayload schema
        DeliveryError: If notification delivery fails (will retry)
    """
```

**Request Example**:
```python
from common_tasks.tasks import send_notification
from common_tasks.schemas import NotificationPayload

payload = NotificationPayload(
    task_id="task-002",
    timestamp="2025-12-25T10:01:30Z",
    source_service="worker",
    notification_id="NOTIF-20251225-xyz789",
    recipient="customer@example.com",
    notification_type="EMAIL",
    subject="Order Confirmation",
    message="Your order ORD-20251225-abc123 has been received.",
    metadata={"order_id": "ORD-20251225-abc123"}
)

result = send_notification.delay(payload.model_dump())
```

**Response Example** (success):
```json
{
    "status": "sent",
    "notification_id": "NOTIF-20251225-xyz789",
    "sent_at": "2025-12-25T10:01:45Z",
    "delivery_id": "msg_abc123xyz"
}
```

**Error Handling**:
- **ValidationError**: Immediate failure, no retry
- **RateLimitError**: Retry with exponential backoff (not implemented in POC)
- **ProviderError**: Retry up to 5 times with 30s delay

**Retry Policy**:
- Max retries: 5
- Retry delay: 30 seconds
- Retry on: Provider errors, network errors
- No retry on: Invalid recipient, validation errors

**Performance**:
- Expected execution time: <1 second
- Timeout: 60 seconds
- Rate limiting: Not implemented in POC (would be post-POC)

---

## Task: health_check (Utility)

**Purpose**: Health check task to verify worker connectivity and queue availability

**Queue**: `default` (low-priority health check queue)

**Signature**:
```python
@celery_app.task(
    name='tasks.health_check',
    queue='default'
)
def health_check() -> dict:
    """
    Health check task for monitoring worker availability.

    Returns:
        dict: Health status
            - status (str): "healthy"
            - timestamp (str): ISO 8601 datetime
            - worker_id (str): Worker that executed task
    """
```

**Request Example**:
```python
from common_tasks.tasks import health_check

result = health_check.delay()
response = result.get(timeout=5)
# {"status": "healthy", "timestamp": "2025-12-25T10:00:00Z", "worker_id": "worker-1@hostname"}
```

**Usage**: Called periodically by monitoring systems to verify workers are responsive

---

## Task Routing

**Queue Configuration**:

```python
# In common/src/common_tasks/celery_app.py
task_routes = {
    'tasks.process_order': {'queue': 'orders'},
    'tasks.send_notification': {'queue': 'notifications'},
    'tasks.health_check': {'queue': 'default'},
}
```

**Worker Queue Assignment**:

```bash
# Order processing workers (high CPU)
celery -A worker.main worker --queues=orders --concurrency=4

# Notification workers (high I/O)
celery -A worker.main worker --queues=notifications --concurrency=8

# General workers (all queues)
celery -A worker.main worker --queues=orders,notifications,default --concurrency=2
```

---

## Serialization

**Format**: JSON (not pickle for security)

**Configuration**:
```python
# In celery_app.py
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
```

**Limitations**:
- Cannot pass Python objects directly (must serialize to dict)
- Datetime objects must be converted to ISO 8601 strings
- Binary data must be base64 encoded

---

## Versioning

**Task Name Versioning** (for breaking changes):

```python
# Version 1 (current)
@celery_app.task(name='tasks.process_order')
def process_order(payload: dict) -> dict:
    pass

# Version 2 (breaking change - would coexist temporarily during migration)
@celery_app.task(name='tasks.process_order.v2')
def process_order_v2(payload: dict) -> dict:
    pass
```

**Migration Strategy**:
1. Add new versioned task alongside old task
2. Update publishers to call new version
3. Drain old queue (wait for pending tasks)
4. Remove old task definition

**POC Note**: Task versioning not implemented in POC; all services update simultaneously per FR-003

---

## Monitoring (Deferred to Post-POC)

**Observability features not in POC**:
- Task execution time tracking
- Success/failure rate metrics
- Queue depth monitoring
- Worker utilization dashboards
- Correlation ID tracing across services

**Post-POC**: Integrate with Celery Flower or custom Prometheus exporter

---

## Security (Deferred to Post-POC)

**Security features not in POC**:
- Task payload encryption
- Message signing/authentication
- Rate limiting per service
- Task authorization (which services can call which tasks)

**POC Assumption**: All services are trusted; no malicious actors

---

## Notes

- Task names use `tasks.` prefix for namespace isolation
- All tasks use `acks_late=True` for crash resilience (FR-011)
- Retry policies are simple linear delays (exponential backoff deferred to post-POC)
- Tasks are idempotent by design (same input → same output, no side effects on retry)
- Error handling distinguishes transient vs permanent failures