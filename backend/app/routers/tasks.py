"""
Task management router.

Handles task batch creation and management endpoints.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.task import TaskBatchRequest, TaskBatchResponse, ParsedTask
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])
logger = logging.getLogger(__name__)


@router.post("/batch", response_model=TaskBatchResponse)
async def create_task_batch(
    request: TaskBatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new task batch and parse individual task items.

    This endpoint accepts raw text input with tasks and automatically
    parses duration information from each line.

    Example input:
    ```
    Buy groceries 30m
    Call mom 15m
    Team meeting 1h
    ```

    Args:
        request: Task batch creation request
        current_user: The authenticated user
        db: Database session

    Returns:
        Created task batch with parsed task items
    """
    task_service = TaskService(db)

    # Create batch and parse tasks via service
    batch, task_items = task_service.create_task_batch(
        user=current_user,
        raw_text=request.raw_text,
        source=request.source,
    )

    # Convert to response format
    parsed_tasks = [
        ParsedTask(
            line_index=item.line_index,
            raw_line=item.raw_line,
            title=item.title,
            duration_minutes=item.parsed_duration_minutes,
            confidence=item.duration_confidence,
            parse_method=item.parse_method,
        )
        for item in task_items
    ]

    logger.info(f"Created task batch {batch.id} with {len(parsed_tasks)} items for user {current_user.id}")

    return TaskBatchResponse(
        batch_id=str(batch.id),
        tasks=parsed_tasks,
    )
