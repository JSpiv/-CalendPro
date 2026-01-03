# Backend Architecture

This document describes the backend architecture and how components interact.

## Architecture Overview

The backend follows a **layered service architecture** where all business logic and database operations are handled by services, and routers only handle HTTP concerns.

```
┌─────────────────────────────────────────────────────────────┐
│                         HTTP Layer                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  main.py   │  │  routers/  │  │  schemas/  │            │
│  │            │  │  - oauth   │  │  - task    │            │
│  │  FastAPI   │  │  - calendar│  │  - calendar│            │
│  │  app       │  │  - events  │  │  - event   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    services/                          │   │
│  │  - TaskService           (task batch operations)     │   │
│  │  - GoogleCalendarService (Google API wrapper)        │   │
│  │  - CalendarSyncService   (sync calendars & events)   │   │
│  │  - EventManagerService   (event CRUD operations)     │   │
│  │  - task_parser           (parse task text)           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                       Data Layer                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  models/   │  │    db/     │  │   core/    │            │
│  │  - user    │  │  - base    │  │  - config  │            │
│  │  - oauth   │  │  - session │  │  - security│            │
│  │  - calendar│  │            │  │            │            │
│  │  - event   │  │            │  │            │            │
│  │  - task    │  │            │  │            │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                    PostgreSQL Database
```

## Layer Responsibilities

### 1. HTTP Layer

#### `main.py`
- FastAPI application setup
- CORS middleware configuration
- Router registration
- Basic health/auth endpoints

#### `routers/`
- **HTTP request/response handling ONLY**
- Input validation (via Pydantic schemas)
- Authentication checks
- Delegates ALL business logic to services
- Returns properly formatted responses

#### `schemas/`
- Pydantic models for API validation
- Request/response type definitions
- Separate from database models

### 2. Business Logic Layer

#### `services/`
All business logic and database operations live here:

**`TaskService`**
- Create task batches
- Parse task items
- Manage task operations

**`GoogleCalendarService`**
- Wrapper around Google Calendar API
- Handle OAuth token management
- CRUD operations on Google Calendar

**`CalendarSyncService`**
- Sync calendars from Google to local DB
- Sync events from Google to local DB
- Handle incremental sync with sync tokens

**`EventManagerService`**
- Create/update/delete events
- Sync changes to Google Calendar
- Query events with filters

**`task_parser`**
- Parse natural language task descriptions
- Extract duration from text

### 3. Data Layer

#### `models/`
- **SQLAlchemy ORM models ONLY**
- No business logic
- Define database schema
- Relationships between tables

#### `db/`
- Database connection management
- Session factory
- Base class for models

#### `core/`
- Configuration (environment variables)
- Security (authentication)
- Shared utilities

## Design Principles

### 1. Service Layer Pattern
✅ **DO:**
- Put all business logic in services
- Put all database operations in services
- Services can call other services
- Services are reusable across endpoints

❌ **DON'T:**
- Put business logic in routers
- Put database queries directly in routers
- Put business logic in models

### 2. Separation of Concerns

**Routers:**
```python
# ✅ GOOD: Router delegates to service
@router.post("/tasks/batch")
async def create_task_batch(request: TaskBatchRequest, ...):
    task_service = TaskService(db)
    batch, items = task_service.create_task_batch(...)
    return format_response(batch, items)
```

```python
# ❌ BAD: Router has business logic
@router.post("/tasks/batch")
async def create_task_batch(request: TaskBatchRequest, ...):
    batch = TaskBatch(...)
    db.add(batch)
    for line in request.raw_text.split("\n"):
        # parsing logic here...
        db.add(task_item)
    db.commit()
```

**Services:**
```python
# ✅ GOOD: Service handles all logic
class TaskService:
    def create_task_batch(self, user, raw_text, source):
        batch = TaskBatch(...)
        self.db.add(batch)
        # ... parsing and database logic ...
        self.db.commit()
        return batch, items
```

### 3. Models Are Pure ORM

```python
# ✅ GOOD: Model is just schema
class User(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(...)
    email: Mapped[str] = mapped_column(...)
```

```python
# ❌ BAD: Model has business logic
class User(Base):
    def create_task_batch(self, text):  # NO!
        # business logic in model
```

## File Organization

```
backend/app/
├── main.py                    # FastAPI app, router registration
├── core/
│   ├── config.py             # Settings, environment variables
│   └── security.py           # Authentication helpers
├── db/
│   ├── base.py               # SQLAlchemy Base class
│   └── session.py            # Database session management
├── models/                    # SQLAlchemy ORM models
│   ├── __init__.py           # Export all models
│   ├── user.py
│   ├── oauth_account.py
│   ├── calendar_source.py
│   ├── external_event.py
│   ├── task_batch.py
│   └── task_item.py
├── schemas/                   # Pydantic validation models
│   ├── __init__.py
│   ├── task.py
│   ├── calendar.py
│   └── event.py
├── services/                  # Business logic layer
│   ├── __init__.py
│   ├── task_service.py
│   ├── task_parser.py
│   ├── google_calendar.py
│   ├── calendar_sync.py
│   └── event_manager.py
└── routers/                   # HTTP endpoint handlers
    ├── __init__.py
    ├── oauth.py
    ├── calendars.py
    └── events.py
```

## Request Flow Example

### Creating a Task Batch

1. **HTTP Request** arrives at router:
   ```
   POST /tasks/batch
   Body: { "raw_text": "Buy groceries 30m\nCall mom 15m" }
   ```

2. **Router** (`main.py`):
   - Validates request via `TaskBatchRequest` schema
   - Authenticates user via `get_current_user`
   - Creates `TaskService` instance
   - Calls `task_service.create_task_batch()`

3. **Service** (`TaskService`):
   - Creates `TaskBatch` model
   - Parses each line via `task_parser`
   - Creates `TaskItem` models
   - Saves to database
   - Returns batch and items

4. **Router** formats response:
   - Converts models to `TaskBatchResponse` schema
   - Returns JSON to client

### Creating a Google Calendar Event

1. **HTTP Request**:
   ```
   POST /events
   Body: { "calendar_source_id": "...", "title": "Meeting", ... }
   ```

2. **Router** (`routers/events.py`):
   - Validates via `EventCreateRequest`
   - Authenticates user
   - Creates `EventManagerService`
   - Calls `event_manager.create_event()`

3. **Service** (`EventManagerService`):
   - Validates calendar ownership
   - Creates `GoogleCalendarService`
   - Calls Google Calendar API
   - Saves to local database
   - Returns event

4. **Router** returns `EventResponse`

## Database Query Pattern

All database queries use SQLAlchemy 2.0 style:

```python
# ✅ GOOD: Modern SQLAlchemy 2.0 style
from sqlalchemy import select

stmt = select(User).where(User.id == user_id)
user = db.execute(stmt).scalar_one_or_none()
```

```python
# ❌ BAD: Legacy SQLAlchemy 1.x style
user = db.query(User).filter(User.id == user_id).first()
```

## Adding New Features

### To add a new endpoint:

1. **Create schema** in `schemas/` for request/response validation
2. **Create or extend service** in `services/` for business logic
3. **Create router** in `routers/` for HTTP handling
4. **Register router** in `main.py`

### Example: Adding a "delete task batch" endpoint

1. **Schema** (`schemas/task.py`):
   ```python
   class TaskBatchDeleteResponse(BaseModel):
       success: bool
       deleted_items: int
   ```

2. **Service** (`services/task_service.py`):
   ```python
   def delete_task_batch(self, batch_id: UUID, user_id: UUID) -> int:
       batch = self.get_task_batch(batch_id, user_id)
       items_count = len(batch.items)
       self.db.delete(batch)
       self.db.commit()
       return items_count
   ```

3. **Router** (in `main.py` or new router file):
   ```python
   @app.delete("/tasks/batch/{batch_id}")
   async def delete_task_batch(
       batch_id: str,
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db),
   ):
       service = TaskService(db)
       deleted = service.delete_task_batch(UUID(batch_id), current_user.id)
       return {"success": True, "deleted_items": deleted}
   ```

## Testing Strategy

### Unit Tests
- Test services in isolation
- Mock database sessions
- Mock external APIs (Google Calendar)

### Integration Tests
- Test routers with test database
- Use FastAPI TestClient
- Verify end-to-end flows

### Example Service Test
```python
def test_create_task_batch():
    db = create_test_db()
    user = create_test_user(db)
    service = TaskService(db)

    batch, items = service.create_task_batch(
        user=user,
        raw_text="Task 1 30m\nTask 2 1h",
        source="test"
    )

    assert len(items) == 2
    assert items[0].parsed_duration_minutes == 30
    assert items[1].parsed_duration_minutes == 60
```

## Environment Variables

Required in `.env`:

```bash
# Database
BACKEND_DATABASE_URL=postgresql://user:pass@localhost/dbname

# Google OAuth (for calendar integration)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/google/callback
```

## Next Steps

1. **Install dependencies**: `cd backend && uv sync`
2. **Set up Google OAuth** credentials in Google Cloud Console
3. **Run migrations**: `alembic upgrade head`
4. **Start server**: `uvicorn app.main:app --reload`
5. **Test endpoints**: See API documentation at `http://localhost:8000/docs`

## Common Patterns

### Creating a new service:
```python
class MyService:
    def __init__(self, db: Session):
        self.db = db

    def my_operation(self, ...):
        # Business logic here
        self.db.add(...)
        self.db.commit()
        return result
```

### Using a service in a router:
```python
@router.post("/my-endpoint")
async def my_endpoint(
    request: MyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = MyService(db)
    result = service.my_operation(...)
    return MyResponse(...)
```

### Querying with ownership check:
```python
stmt = (
    select(Resource)
    .join(User)
    .where(
        Resource.id == resource_id,
        User.id == user_id
    )
)
resource = db.execute(stmt).scalar_one_or_none()
if not resource:
    raise ValueError("Not found or access denied")
```
