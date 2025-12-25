# Data Model: Microservices Repository Structure

**Feature**: 001-microservices-structure
**Date**: 2025-12-25
**Domain**: Task Queue Communication

## Overview

This feature focuses on **repository structure** rather than business domain data models. The data model here defines **task payload schemas** used for inter-service communication via Celery task queues.

---

## Core Entities

### TaskPayload (Base)

**Purpose**: Base class for all task payloads to ensure consistent structure

**Fields**:
- `task_id` (string, required): Unique identifier for task execution tracking
- `timestamp` (datetime, required): When task was created
- `source_service` (string, required): Which service initiated the task

**Validation**:
- `task_id` must be non-empty string
- `timestamp` must be valid ISO 8601 datetime
- `source_service` must match pattern `^[a-z0-9-]+$`

**State**: Immutable (tasks are stateless, payload doesn't change)

**Implementation**: Pydantic BaseModel in `common/src/common_tasks/schemas.py`

---

### OrderPayload (Example)

**Purpose**: Example task payload for order processing workflow (example-service-1 → worker)

**Inherits**: TaskPayload

**Fields**:
- `order_id` (string, required): Unique order identifier
- `customer_id` (string, required): Customer who placed order
- `items` (list[dict], required): Order line items with product_id and quantity
- `total_amount` (float, required): Total order value
- `priority` (enum, optional): Order priority (LOW, NORMAL, HIGH), defaults to NORMAL

**Validation**:
- `order_id` format: `ORD-{timestamp}-{random}`
- `total_amount` must be positive
- `items` list must have at least 1 item
- Each item must have `product_id` (string) and `quantity` (positive integer)

**Usage**:
```python
# example-service-1 publishes task with OrderPayload
from common_tasks.schemas import OrderPayload
from common_tasks.tasks import process_order

payload = OrderPayload(
    task_id="task-123",
    timestamp="2025-12-25T10:00:00Z",
    source_service="example-service-1",
    order_id="ORD-20251225-abc123",
    customer_id="CUST-456",
    items=[{"product_id": "PROD-789", "quantity": 2}],
    total_amount=99.98
)
process_order.delay(payload.model_dump())
```

**State Transitions**: N/A (stateless task payload)

---

### NotificationPayload (Example)

**Purpose**: Example task payload for notification delivery (worker → example-service-2)

**Inherits**: TaskPayload

**Fields**:
- `notification_id` (string, required): Unique notification identifier
- `recipient` (string, required): Notification recipient (email, phone, user ID)
- `notification_type` (enum, required): Type of notification (EMAIL, SMS, PUSH)
- `subject` (string, optional): Notification subject line (for EMAIL type)
- `message` (string, required): Notification message content
- `metadata` (dict, optional): Additional context data

**Validation**:
- `notification_id` format: `NOTIF-{timestamp}-{random}`
- `recipient` must be non-empty string
- `notification_type` must be one of: EMAIL, SMS, PUSH
- `message` max length: 10,000 characters
- If `notification_type` is EMAIL, `subject` is required

**Usage**:
```python
# Worker triggers notification after processing order
from common_tasks.schemas import NotificationPayload
from common_tasks.tasks import send_notification

payload = NotificationPayload(
    task_id="task-456",
    timestamp="2025-12-25T10:05:00Z",
    source_service="worker",
    notification_id="NOTIF-20251225-xyz789",
    recipient="customer@example.com",
    notification_type="EMAIL",
    subject="Order Confirmation",
    message="Your order ORD-20251225-abc123 has been received.",
    metadata={"order_id": "ORD-20251225-abc123"}
)
send_notification.delay(payload.model_dump())
```

**State Transitions**: N/A (stateless task payload)

---

## Entity Relationships

```
TaskPayload (base)
    ↑
    ├── OrderPayload (example-service-1 → worker)
    ├── NotificationPayload (worker → example-service-2)
    └── [Future payloads inherit from base]
```

**Relationships**:
- OrderPayload and NotificationPayload are **independent** (no direct FK relationships)
- Linked only via shared `task_id` or `metadata` fields for correlation
- Services don't share databases - communication is **only** via task payloads

---

## Schema Evolution Strategy

### Adding New Fields (Non-Breaking)

- Add optional fields with defaults to existing payloads
- Update `common_tasks` module version (MINOR bump)
- All services rebuild with new common module
- Old tasks with missing fields still validate (defaults applied)

### Removing/Renaming Fields (Breaking)

- Requires MAJOR version bump of `common_tasks` module
- **All services MUST update simultaneously** (per FR-003 requirement)
- Deployment sequence:
  1. Stop all workers
  2. Update common module in all services
  3. Rebuild and redeploy all services
  4. Restart workers

### Versioning Example

```python
# common_tasks v1.0.0
class OrderPayload(TaskPayload):
    order_id: str
    total_amount: float

# common_tasks v1.1.0 (non-breaking)
class OrderPayload(TaskPayload):
    order_id: str
    total_amount: float
    discount_code: Optional[str] = None  # Added, optional with default

# common_tasks v2.0.0 (breaking)
class OrderPayload(TaskPayload):
    order_id: str
    total_amount: float
    line_items: list[LineItem]  # Changed from `items` (breaking)
```

---

## Validation Rules

### Cross-Field Validation

- If `OrderPayload.priority == HIGH`, task timeout should be reduced (configured in worker, not schema)
- If `NotificationPayload.notification_type == EMAIL`, `subject` field is required

### Serialization

- All payloads serialize to JSON via Pydantic's `model_dump()`
- Celery serializer configured to JSON (no pickle for security)
- Datetime fields serialize to ISO 8601 strings

---

## Storage Considerations

**No persistent storage in POC** - Task payloads are:
- Stored temporarily in Redis (broker queue + result backend)
- Expired after task completion (configurable TTL)
- Not persisted to database

**Post-POC**: Could add task persistence for audit trail:
- PostgreSQL for task history
- Elasticsearch for task search/analytics
- S3 for payload archival

---

## Notes

- This is a **POC data model** - real services would have more complex payloads
- Example payloads demonstrate patterns (order processing → notification)
- Services can define additional payload types by inheriting from `TaskPayload`
- Pydantic provides runtime validation, type hints for IDE support, and JSON schema generation