"""Бизнес логика задач и календаря."""

import logging
from datetime import datetime
from typing import Optional, List

from fastapi import HTTPException, status

from src.repositories import (
    TaskRepository,
    CategoryRepository,
    ProjectRepository,
    UserRepository,
)
from src.models.user import User
from src.models.task import Task, TaskStatus, ImportanceLevel
from src.schemas import (
    CreateTaskRequest,
)


logger = logging.getLogger(__name__)


class TaskService:
    
    def __init__(self, session):
        self.session = session
        self.task_repo = TaskRepository(session)
        self.category_repo = CategoryRepository(session)
        self.project_repo = ProjectRepository(session)
        self.user_repo = UserRepository(session)
    
    async def get_assigned_tasks(
        self,
        user: User,
        status_filter: Optional[TaskStatus] = None,
        importance_filter: Optional[ImportanceLevel] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        offset = (page - 1) * page_size
        
        tasks, total = await self.task_repo.get_assigned_tasks(
            user_id=user.id,
            status_filter=status_filter,
            importance_filter=importance_filter,
            limit=page_size,
            offset=offset,
        )
        
        completed_count = await self.task_repo.count_assigned_tasks(
            user_id=user.id,
            status_filter=TaskStatus.COMPLETED,
        )
        
        return {
            "total": total,
            "completed": completed_count,
            "tasks": tasks,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
    
    async def get_task(
        self,
        task_id: int,
        user: User,
    ) -> Task:
        task = await self.task_repo.get_task_with_relations(task_id)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача не найдена",
            )
        
        is_assignee = task.assignee_id == user.id
        is_creator = task.created_by_id == user.id
        
        if not is_assignee and not is_creator:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ к задаче запрещен",
            )
        
        if is_assignee and not is_creator:
            task.project_name = None
            task.category_marker = None
        else:
            if task.project:
                task.project_name = task.project.name
            if task.category:
                task.category_marker = f"{task.category.color} {task.category.name}"
        
        return task
    
    async def complete_task(self, task_id: int, user: User) -> dict:
        task = await self.task_repo.get_task_with_relations(task_id)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача не найдена",
            )
        
        if task.assignee_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Выполнить эту задачу может только назначенный сотрудник",
            )
        
        task.mark_completed()
        await self.session.flush()
        
        return {"detail": "Задача помечена как выполненая"}
    
    async def reset_filters(self, user: User) -> dict:
        return {"detail": "Фильтры успешно сброшены"}
    
    async def create_calendar_task(
        self,
        user: User,
        data: CreateTaskRequest,
    ) -> Task:
        if data.category_id:
            category = await self.category_repo.get_by_id_and_user(
                data.category_id, user.id
            )
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Категория не найдена",
                )
        
        if data.project_id:
            project = await self.project_repo.get_by_id(data.project_id)
            if not project or project.owner_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Проект не найден",
                )
        
        if data.assignee_id:
            assignee = await self.user_repo.get_by_id(data.assignee_id)
            if not assignee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Исполнитель не найден",
                )
        
        task = await self.task_repo.create(
            name=data.name,
            description=data.description,
            category_id=data.category_id,
            project_id=data.project_id,
            assignee_id=data.assignee_id,
            created_by_id=user.id,
            deadline=data.deadline,
            importance=data.importance,
            status=TaskStatus.PENDING,
        )
        
        return task


class CalendarService:

    def __init__(self, session):
        self.session = session
        self.task_repo = TaskRepository(session)
    
    async def get_calendar_month(
        self,
        user: User,
        year: int,
        month: int,
    ) -> dict:
        tasks = await self.task_repo.get_tasks_for_calendar_month(
            user_id=user.id,
            year=year,
            month=month,
        )
        
        date_marks = {}
        for task in tasks:
            if task.deadline:
                date_str = task.deadline.strftime("%Y-%m-%d")
                if date_str not in date_marks:
                    date_marks[date_str] = {
                        "date": date_str,
                        "task_count": 0,
                        "has_important": False,
                    }
                date_marks[date_str]["task_count"] += 1
                if task.importance in [ImportanceLevel.CRITICAL, ImportanceLevel.HIGH]:
                    date_marks[date_str]["has_important"] = True
        
        return {
            "year": year,
            "month": month,
            "dates": list(date_marks.values()),
        }
    
    async def get_calendar_day_tasks(
        self,
        user: User,
        date: str,
        importance_filter: Optional[ImportanceLevel] = None,
        status_filter: Optional[TaskStatus] = None,
    ) -> dict:
        try:
            target_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не верный формат даты. (YYYY-MM-DD)",
            )
        
        tasks = await self.task_repo.get_tasks_for_calendar_day(
            user_id=user.id,
            target_date=target_date,
            importance_filter=importance_filter,
            status_filter=status_filter,
        )
        
        return {
            "date": date,
            "tasks": tasks,
        }
