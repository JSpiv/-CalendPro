from typing import Optional
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.parser import parse_task_line
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.task_batch import TaskBatch
from app.models.task_item import TaskItem

app = FastAPI()

# allow Next.js dev server
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # Required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Test endpoint to verify authentication.
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
    }


# Pydantic models for task batch API
class TaskBatchRequest(BaseModel):
    raw_text: str
    source: str = "notepad"


class ParsedTask(BaseModel):
    line_index: int
    raw_line: str
    title: str
    duration_minutes: int
    confidence: float
    parse_method: str


class TaskBatchResponse(BaseModel):
    batch_id: str
    tasks: list[ParsedTask]


@app.post("/tasks/batch", response_model=TaskBatchResponse)
async def create_task_batch(
    request: TaskBatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new task batch and parse individual task items.
    """
    # Create the batch
    batch = TaskBatch(
        user_id=current_user.id,
        raw_text=request.raw_text,
        source=request.source,
    )
    db.add(batch)
    db.flush()  # Get the batch.id without committing

    # Parse each line
    lines = request.raw_text.split("\n")
    parsed_tasks = []

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
        db.add(task_item)

        parsed_tasks.append(
            ParsedTask(
                line_index=idx,
                raw_line=line,
                title=title,
                duration_minutes=duration_minutes,
                confidence=confidence,
                parse_method=parse_method,
            )
        )

    db.commit()

    return TaskBatchResponse(
        batch_id=str(batch.id),
        tasks=parsed_tasks,
    )
