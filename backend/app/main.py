from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.security import get_current_user
from app.models.user import User

# Import routers
from app.routers import oauth, calendars, events, tasks

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

# Include routers
app.include_router(oauth.router)
app.include_router(calendars.router)
app.include_router(events.router)
app.include_router(tasks.router)


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
