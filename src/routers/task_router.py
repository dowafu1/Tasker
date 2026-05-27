"""Ручки задач"""

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
    summary="Получайте назначенные задания",
    description="Получите список задач, назначенных текущему пользователю.",
    responses={
        200: {"description": "Задачи успешно получены"},
        401: {"model": ErrorResponse, "description": "Не подтверждено"},
    },
)
async def get_assigned_tasks(
    status: Optional[TaskStatus] = Query(None, description="Фильтр по статусу"),
    importance: Optional[ImportanceLevel] = Query(None, description="Фильтр по важности"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Количество элементов на странице"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
    summary="Получить подробную информацию о задании",
    description="Получить полную карточку задачи",
    responses={
        200: {"description": "Задача успешно получена."},
        401: {"model": ErrorResponse, "description": "Не подтверждено"},
        403: {"model": ErrorResponse, "description": "Доступ запрещен"},
        404: {"model": ErrorResponse, "description": "Задача не найдена"},
    },
)
async def get_task(
    task_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TaskService(session)
    task = await service.get_task(task_id, current_user)
    return task


@router.patch(
    "/tasks/{task_id}/complete",
    summary="Выполните задачу",
    description="Отметьте задачу как выполненную. Выполнить задачу может только назначенный исполнитель.",
    responses={
        200: {"description": "Задача отмечена как выполненная"},
        401: {"model": ErrorResponse, "description": "Не подтверждено"},
        403: {"model": ErrorResponse, "description": "Только исполнитель может завершить"},
        404: {"model": ErrorResponse, "description": "Задача не найдена"},
    },
)
async def complete_task(
    task_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TaskService(session)
    return await service.complete_task(task_id, current_user)


@router.post(
    "/tasks/filters/reset",
    summary="Сбросить фильтры задач",
    description="Сбросить все примененные фильтры задач.",
    responses={
        200: {"description": "Фильтры успешно сброшены."},
        401: {"model": ErrorResponse, "description": "Не подтверждено"},
    },
)
async def reset_filters(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TaskService(session)
    return await service.reset_filters(current_user)


# CALENDAR ENDPOINTS

@router.get(
    "/calendar/{year}/{month}",
    response_model=CalendarMonthResponse,
    summary="Получить календарный месяц",
    description="Получите календарный вид для конкретного месяца с отметками дат, отображающими количество задач..",
    responses={
        200: {"description": "Календарные данные успешно получены."},
        401: {"model": ErrorResponse, "description": "Не подтверждено"},
    },
)
async def get_calendar_month(
    year: int,
    month: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CalendarService(session)
    return await service.get_calendar_month(current_user, year, month)


@router.get(
    "/calendar/{date}/tasks",
    response_model=CalendarDayTasksResponse,
    summary="Получить задачи на календарный день",
    description="Получайте задачи на определенную дату с возможностью добавления фильтров.",
    responses={
        200: {"description": "Задачи успешно получены"},
        400: {"model": ErrorResponse, "description": "Неверный формат даты"},
        401: {"model": ErrorResponse, "description": "Не подтверждено"},
    },
)
async def get_calendar_day_tasks(
    date: str,
    importance: Optional[ImportanceLevel] = Query(None, description="Фильтр по важности"),
    status: Optional[TaskStatus] = Query(None, description="Фильтр по статусу"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
    summary="Создать задачу через календарь",
    description="Создайте новую задачу из календаря.",
    responses={
        200: {"description": "Задача успешно создана"},
        400: {"model": ErrorResponse, "description": "Ошибка валидации"},
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        404: {"model": ErrorResponse, "description": "Категория/Проект/Исполнитель не найден"},
    },
)
async def create_calendar_task(
    request: CreateTaskRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TaskService(session)
    task = await service.create_calendar_task(current_user, request)
    return task
