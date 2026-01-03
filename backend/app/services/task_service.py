"""
Task batch and task item service.

Handles all business logic for creating and managing task batches.
"""

from typing import List
from uuid import UUID
import logging

from sqlalchemy.orm import Session

from app.models.task_batch import TaskBatch
from app.models.task_item import TaskItem
from app.models.user import User
from app.services.task_parser import parse_task_line

logger = logging.getLogger(__name__)


class TaskService:
    """Service for managing task batches and items."""

    def __init__(self, db: Session):
        """
        Initialize the task service.

        Args:
            db: Database session
        """
        self.db = db

    def create_task_batch(
        self,
        user: User,
        raw_text: str,
        source: str = "notepad"
    ) -> tuple[TaskBatch, List[TaskItem]]:
        """
        Create a new task batch and parse individual task items.

        Args:
            user: The user creating the batch
            raw_text: Raw text input with tasks
            source: Source of the tasks (e.g., "notepad", "mobile")

        Returns:
            Tuple of (TaskBatch, List[TaskItem])
        """
        # Create the batch
        batch = TaskBatch(
            user_id=user.id,
            raw_text=raw_text,
            source=source,
        )
        self.db.add(batch)
        self.db.flush()  # Get the batch.id without committing

        # Parse each line
        lines = raw_text.split("\n")
        task_items = []

        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            title, duration_minutes, confidence, parse_method = parse_task_line(line)

            if not title:
                continue

            task_item = TaskItem(
                batch_id=batch.id,
                line_index=idx,
                raw_line=line,
                title=title,
                parsed_duration_minutes=duration_minutes,
                duration_confidence=confidence,
                parse_method=parse_method,
            )
            self.db.add(task_item)
            task_items.append(task_item)

        self.db.commit()

        logger.info(f"Created task batch {batch.id} with {len(task_items)} items for user {user.id}")

        return batch, task_items

    def get_task_batch(self, batch_id: UUID, user_id: UUID) -> TaskBatch:
        """
        Get a task batch by ID, verifying ownership.

        Args:
            batch_id: The batch UUID
            user_id: The user UUID (for ownership check)

        Returns:
            TaskBatch object

        Raises:
            ValueError: If batch not found or user doesn't own it
        """
        batch = self.db.query(TaskBatch).filter(
            TaskBatch.id == batch_id,
            TaskBatch.user_id == user_id
        ).first()

        if not batch:
            raise ValueError(f"Task batch {batch_id} not found or access denied")

        return batch

    def get_user_batches(self, user_id: UUID, limit: int = 50) -> List[TaskBatch]:
        """
        Get recent task batches for a user.

        Args:
            user_id: The user UUID
            limit: Maximum number of batches to return

        Returns:
            List of TaskBatch objects
        """
        batches = self.db.query(TaskBatch).filter(
            TaskBatch.user_id == user_id
        ).order_by(
            TaskBatch.created_at.desc()
        ).limit(limit).all()

        return batches
