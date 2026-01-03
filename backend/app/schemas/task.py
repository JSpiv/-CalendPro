"""
Pydantic schemas for task-related API endpoints.
"""

from pydantic import BaseModel


class TaskBatchRequest(BaseModel):
    """Request to create a new task batch."""

    raw_text: str
    source: str = "notepad"


class ParsedTask(BaseModel):
    """A single parsed task from a batch."""

    line_index: int
    raw_line: str
    title: str
    duration_minutes: int
    confidence: float
    parse_method: str


class TaskBatchResponse(BaseModel):
    """Response from creating a task batch."""

    batch_id: str
    tasks: list[ParsedTask]
