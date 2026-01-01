# Calendar App

## Description

A full-stack calendar and task management application with intelligent task parsing and planning features. Built with modern web technologies and designed for efficient time management and productivity.

## Features

- **Calendar Management** - View and manage your events and tasks in a calendar interface
- **Task Management** - Create, organize, and track tasks with tags and batches
- **Natural Language Parsing** - Parse natural language input into structured tasks
- **Planning System** - Create and export task plans with time blocking
- **Authentication** - Secure user authentication with OAuth support
- **External Calendar Integration** - Connect and sync with external calendar sources
- **User Preferences** - Customizable user settings and preferences

## Tech Stack

### Frontend
- **Next.js 14+** - React framework with App Router
- **TypeScript** - Type-safe development
- **Auth.js (NextAuth)** - Authentication
- **Prisma** - Database ORM
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components
- **pnpm** - Package management

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **Alembic** - Database migrations
- **PostgreSQL** - Primary database
- **Pydantic** - Data validation
- **uv** - Python package management

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **PostgreSQL** - Database server

## Installation

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ and pnpm
- Python 3.11+ and uv

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd calendar_app
```

2. Start the database with Docker:
```bash
docker compose up -d
```

3. Set up the backend:
```bash
cd backend
uv sync
uv run alembic upgrade head
```

4. Set up the frontend:
```bash
cd frontend
pnpm install
pnpm prisma generate
```

5. Configure environment variables:
   - Create `.env` files in both `backend/` and `frontend/` directories
   - Add necessary configuration (database URLs, API keys, etc.)

## Usage

### Development

Run the backend server:
```bash
cd backend
uv run uvicorn app.main:app --reload
```

Run the frontend development server:
```bash
cd frontend
pnpm dev
```

Access the application at `http://localhost:3000`

### Docker

Run the entire stack with Docker Compose:
```bash
docker compose up -d --build
```
