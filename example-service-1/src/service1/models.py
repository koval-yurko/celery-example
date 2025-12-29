"""
Pydantic Models for Service 1 API Endpoints

Request and response models for task submission, status, and history endpoints.
"""

import json
from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, model_validator


# Request Models

class AddTaskRequest(BaseModel):
    """Addition task submission request"""
    x: int | float = Field(..., description="First operand")
    y: int | float = Field(..., description="Second operand")


class LongRunningTaskRequest(BaseModel):
    """Long-running task submission request"""
    duration: int = Field(..., ge=1, le=300, description="Duration in seconds")


class ProcessDataRequest(BaseModel):
    """Data processing task submission request"""
    data: dict[str, Any] = Field(..., description="JSON object to process")

    @model_validator(mode='after')
    def validate_size(self) -> 'ProcessDataRequest':
        """Validate payload size <= 1MB"""
        size = len(json.dumps(self.data).encode('utf-8'))
        if size > 1_048_576:  # 1MB
            raise ValueError(f"Payload size {size} bytes exceeds 1MB limit")
        return self


# Response Models (only task submission - query responses moved to API Gateway)

class TaskSubmissionResponse(BaseModel):
    """Standardized response for task submission (HTTP 202)"""
    status: Literal["accepted"] = Field(..., description="Submission status")
    task_id: str = Field(..., description="Celery task ID (UUID)")
    task_type: str = Field(..., description="Task name/type")
    submitted_at: datetime = Field(..., description="Submission timestamp (ISO 8601)")
    message: str = Field(..., description="Human-readable status message")


# NOTE: Task query response models (TaskStatusResponse, TaskResultResponse,
# TaskHistoryEntry, TaskHistoryResponse, ErrorResponse) have been moved to
# api-gateway/src/api_gateway/models.py to avoid duplication
