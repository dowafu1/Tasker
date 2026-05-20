"""Main FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.core.database import init_db, close_db
from src.routers.auth_router import router as auth_router
from src.routers.profile_router import router as profile_router
from src.routers.project_router import router as project_router
from src.routers.task_router import router as task_router


# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting up Task Manager API...")
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Task Manager API...")
    await close_db()
    logger.info("Database connections closed")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Task Manager API

A comprehensive task management backend with:

### Authentication & Authorization
- User registration and login with JWT tokens
- Password recovery via email codes
- Token refresh rotation

### Profile Management
- View and update user profile
- Change password
- Avatar upload support

### Projects
- Create, update, delete projects
- Project ownership and access control

### Tasks
- Assigned tasks with filtering and pagination
- Task completion tracking
- Calendar integration

### Calendar
- Monthly calendar view with task markers
- Daily task views with filters
- Create tasks from calendar

**Important Importance Markers:**
- 🔴 Critical (очень срочно)
- 🟠 High (срочно)
- 🟡 Medium (может подождать)
- 🟢 Low (несрочно)
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# CORS middleware (configure origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler for consistent error format
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions with consistent error format."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "code": "INTERNAL_ERROR",
        },
    )


# Include routers
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(project_router)
app.include_router(task_router)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - health check."""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
