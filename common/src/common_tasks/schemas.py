"""
Task Payload Schemas

Pydantic models for task payloads ensuring type safety and validation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class TaskPayload(BaseModel):
    """Base class for all task payloads"""

    task_id: str = Field(..., description="Unique identifier for task execution tracking")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When task was created")
    source_service: str = Field(..., description="Which service initiated the task")

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, v):
        if not v or not v.strip():
            raise ValueError("task_id must be non-empty")
        return v

    @field_validator("source_service")
    @classmethod
    def validate_source_service(cls, v):
        if not v or not v.strip():
            raise ValueError("source_service must be non-empty")
        return v


class OrderPriority(str, Enum):
    """Order priority levels"""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"


class OrderPayload(TaskPayload):
    """Task payload for order processing workflow"""

    order_id: str = Field(..., description="Unique order identifier")
    customer_id: str = Field(..., description="Customer who placed order")
    items: list[dict] = Field(..., description="Order line items with product_id and quantity")
    total_amount: float = Field(..., description="Total order value", gt=0)
    priority: OrderPriority = Field(default=OrderPriority.NORMAL, description="Order priority")

    @field_validator("items")
    @classmethod
    def validate_items(cls, v):
        if not v:
            raise ValueError("items list must have at least 1 item")
        for item in v:
            if "product_id" not in item or "quantity" not in item:
                raise ValueError("Each item must have product_id and quantity")
            if not isinstance(item["quantity"], int) or item["quantity"] <= 0:
                raise ValueError("quantity must be a positive integer")
        return v


class NotificationType(str, Enum):
    """Notification delivery types"""

    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"


class NotificationPayload(TaskPayload):
    """Task payload for notification delivery"""

    notification_id: str = Field(..., description="Unique notification identifier")
    recipient: str = Field(..., description="Notification recipient (email, phone, user ID)")
    notification_type: NotificationType = Field(..., description="Type of notification")
    subject: Optional[str] = Field(None, description="Notification subject line (for EMAIL type)")
    message: str = Field(..., description="Notification message content", max_length=10000)
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional context data")

    @field_validator("recipient")
    @classmethod
    def validate_recipient(cls, v):
        if not v or not v.strip():
            raise ValueError("recipient must be non-empty")
        return v

    def model_post_init(self, __context):
        """Validate that EMAIL notifications have a subject"""
        if self.notification_type == NotificationType.EMAIL and not self.subject:
            raise ValueError("subject is required for EMAIL notifications")