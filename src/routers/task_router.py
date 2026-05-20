"""Task router."""

from typing import Optional, List
from datetime import date

from fastapi import APIRouter, Depends, Query

from src.core.database import AsyncSession, get_db
from src.core.security import get_current_user
from src.models.user import User
from src.models.task import TaskStatus, ImportanceLevel
from src.schemas import (
    TaskResponse,
    AssignedTasksResponse,
    TaskListItem,
    CreateTaskRequest,
    CalendarMonthResponse,
    CalendarDayTasksResponse,
    ErrorResponse,
)
from src.services import TaskService, CalendarService


router = APIRouter(prefix="/api/v1", tags=["Tasks"])


@router.get(
    "/tasks/assigned",
    response_model=AssignedTasksResponse,
    summary="Get assigned tasks",
    description="Get list of tasks assigned to current user with counters and pagination.",
    responses={
        200: {"description": "Tasks retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def get_assigned_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    importance: Optional[ImportanceLevel] = Query(None, description="Filter by importance"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get assigned tasks with filters and pagination."""
    service = TaskService(session)
    result = await service.get_assigned_tasks(
        current_user,
        status_filter=status,
        importance_filter=importance,
        page=page,
        page_size=page_size,
    )
    return result


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Get task details",
    description="Get full task card. Conditional logic: if task is assigned (not created by user), project_name and category_marker are omitted.",
    responses={
        200: {"description": "Task retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
async def get_task(
    task_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get task details with conditional field display."""
    service = TaskService(session)
    task = await service.get_task(task_id, current_user)
    return task


@router.patch(
    "/tasks/{task_id}/complete",
    summary="Complete task",
    description="Mark a task as completed. Only assignee can complete the task.",
    responses={
        200: {"description": "Task marked as completed"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Only assignee can complete"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
async def complete_task(
    task_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark task as completed."""
    service = TaskService(session)
    return await service.complete_task(task_id, current_user)


@router.post(
    "/tasks/filters/reset",
    summary="Reset task filters",
    description="Reset all applied task filters.",
    responses={
        200: {"description": "Filters reset successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def reset_filters(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reset task filters."""
    service = TaskService(session)
    return await service.reset_filters(current_user)


# ============================================================================
# CALENDAR ENDPOINTS
# ============================================================================

@router.get(
    "/calendar/{year}/{month}",
    response_model=CalendarMonthResponse,
    summary="Get calendar month",
    description="Get calendar view for a specific month with date marks showing task counts.",
    responses={
        200: {"description": "Calendar data retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def get_calendar_month(
    year: int,
    month: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get calendar month with task date marks."""
    service = CalendarService(session)
    return await service.get_calendar_month(current_user, year, month)


@router.get(
    "/calendar/{date}/tasks",
    response_model=CalendarDayTasksResponse,
    summary="Get calendar day tasks",
    description="Get tasks for a specific date with optional filters.",
    responses={
        200: {"description": "Tasks retrieved successfully"},
        400: {"model": ErrorResponse, "description": "Invalid date format"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def get_calendar_day_tasks(
    date: str,
    importance: Optional[ImportanceLevel] = Query(None, description="Filter by importance"),
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get tasks for a specific calendar day."""
    service = CalendarService(session)
    return await service.get_calendar_day_tasks(
        current_user,
        date,
        importance_filter=importance,
        status_filter=status,
    )


@router.post(
    "/calendar/tasks",
    response_model=TaskResponse,
    summary="Create task via calendar",
    description="Create a new task from calendar view.",
    responses={
        200: {"description": "Task created successfully"},
        400: {"model": ErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Category/Project/Assignee not found"},
    },
)
async def create_calendar_task(
    request: CreateTaskRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new task via calendar."""
    service = TaskService(session)
    task = await service.create_calendar_task(current_user, request)
    return task
