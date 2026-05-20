from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import date
from api.deps import get_current_user, get_db
from models.user import User
from schemas.task import TaskCreate, TaskResponse, TaskAssignedResponse, TaskComplete, PriorityEnum
from services.task import TaskService
from repositories.task import TaskRepository

router = APIRouter()


@router.get("/tasks/assigned", response_model=List[TaskAssignedResponse])
async def get_assigned_tasks(
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    priority: Optional[PriorityEnum] = Query(None, description="Filter by priority"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = TaskService(TaskRepository(db))
    tasks = await service.get_assigned_tasks(current_user.id, completed)
    return tasks

@router.get("/tasks/assigned/count")
async def get_assigned_tasks_count(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = TaskService(TaskRepository(db))
    tasks = await service.get_assigned_tasks(current_user.id)
    total = len(tasks)
    completed = sum(1 for t in tasks if t.is_completed)
    return {"total": total, "completed": completed}

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = TaskService(TaskRepository(db))
    task = await service.get_task(task_id)
    if not task:
        return {"error": "Task not found"}
    return task

@router.patch("/tasks/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: int, data: TaskComplete, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = TaskService(TaskRepository(db))
    return await service.complete_task(task_id, data)

# Календарь
@router.get("/calendar/month")
async def get_calendar_month(year: int, month: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    days = []
    return {"year": year, "month": month, "days": days}

@router.get("/calendar/tasks", response_model=List[TaskResponse])
async def get_tasks_by_date(
    date: date,
    priority: Optional[PriorityEnum] = None,
    status: Optional[str] = Query(None, description="in_progress or completed"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = TaskService(TaskRepository(db))
    tasks = await service.get_tasks_by_date(current_user.id, date)
    return tasks

@router.post("/calendar/tasks", response_model=TaskResponse)
async def create_task_via_calendar(data: TaskCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = TaskService(TaskRepository(db))
    return await service.create_task(current_user.id, data)