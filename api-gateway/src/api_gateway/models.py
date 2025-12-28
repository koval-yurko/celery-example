"""
Pydantic Models for API Gateway Task Query Endpoints

Shared response models for task status, result, and history queries.
These models are used by the API Gateway to query task state from the
shared Redis result backend, regardless of which service submitted the task.
"""

from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


# Response Models

class TaskSubmissionResponse(BaseModel):
    """Standardized response for task submission (HTTP 202)"""
    status: Literal["accepted"] = Field(..., description="Submission status")
    task_id: str = Field(..., description="Celery task ID (UUID)")
    task_type: str = Field(..., description="Task name/type")
    submitted_at: datetime = Field(..., description="Submission timestamp (ISO 8601)")
    message: str = Field(..., description="Human-readable status message")


class TaskStatusResponse(BaseModel):
    """Task status query response (HTTP 200)"""
    task_id: str = Field(..., description="Celery task ID")
    task_type: Optional[str] = Field(None, description="Task name if available")
    state: Literal["PENDING", "STARTED", "PROGRESS", "SUCCESS", "FAILURE", "RETRY", "REVOKED"] = Field(..., description="Current task state")
    progress: Optional[dict[str, Any]] = Field(None, description="Progress metadata (for PROGRESS state)")
    submitted_at: Optional[datetime] = Field(None, description="When task was submitted")
    started_at: Optional[datetime] = Field(None, description="When task started executing")
    completed_at: Optional[datetime] = Field(None, description="When task finished (success or failure)")


class TaskResultResponse(BaseModel):
    """Task result retrieval response (HTTP 200)"""
    task_id: str = Field(..., description="Celery task ID")
    task_type: Optional[str] = Field(None, description="Task name if available")
    state: Literal["SUCCESS", "FAILURE", "PENDING", "STARTED"] = Field(..., description="Final task state")
    result: Optional[Any] = Field(None, description="Task return value (if SUCCESS)")
    error: Optional[str] = Field(None, description="Error message (if FAILURE)")
    traceback: Optional[str] = Field(None, description="Exception traceback (if FAILURE)")
    submitted_at: Optional[datetime] = Field(None, description="Submission timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")


class TaskHistoryEntry(BaseModel):
    """Single task entry in history list"""
    task_id: str = Field(..., description="Celery task ID")
    task_type: Optional[str] = Field(None, description="Task name")
    state: str = Field(..., description="Current state")
    submitted_at: Optional[datetime] = Field(None, description="Submission timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp (if finished)")
    result_summary: Optional[str] = Field(None, description="Brief result or error summary")


class TaskHistoryResponse(BaseModel):
    """Task history listing response (HTTP 200)"""
    tasks: list[TaskHistoryEntry] = Field(..., description="List of all tasks")
    total_count: int = Field(..., description="Total number of tasks")
    timestamp: datetime = Field(..., description="When history was retrieved")


class ErrorResponse(BaseModel):
    """Standardized error response (HTTP 400/404/500/503)"""
    error: str = Field(..., description="Error type/category")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[dict[str, Any]] = Field(None, description="Additional error context")
    task_id: Optional[str] = Field(None, description="Task ID if applicable (404 errors)")
    timestamp: datetime = Field(..., description="Error occurrence timestamp")
