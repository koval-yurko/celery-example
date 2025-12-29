"""
Pydantic Models for Service 2 API Endpoints

Request and response models for task submission, status, and history endpoints.
"""

from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


# Request Models

class MultiplyTaskRequest(BaseModel):
    """Multiplication task submission request"""
    x: int | float = Field(..., description="First operand")
    y: int | float = Field(..., description="Second operand")


class ProgressTaskRequest(BaseModel):
    """Progress-tracked task submission request"""
    iterations: int = Field(..., ge=1, le=1000, description="Number of iterations")


class ConfigurableOutcomeTaskRequest(BaseModel):
    """Configurable outcome task submission request (NEW)"""
    duration: int = Field(..., ge=1, le=300, description="Duration in seconds")
    should_succeed: bool = Field(..., description="True for success, False for failure")


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
