from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
import asyncio
from .config import app_config
from .routers.auth_router import router as auth_router
from .routers.profile_router import router as profile_router
from .routers.project_router import router as project_router
from .routers.task_router import router as task_router

app = FastAPI()

# Include routers
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(project_router)
app.include_router(task_router)

@app.on_event("startup")
async def startup():
    # Add any startup logic here, e.g., database connection
    pass

@app.on_event("shutdown")
async def shutdown():
    # Add any shutdown logic here, e.g., closing database connections
    passuvicorn main:app --reload --host 127.0.0.1 --port 8000