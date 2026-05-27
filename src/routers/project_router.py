"""Ручки проекта"""

from typing import List

from fastapi import APIRouter, Depends

from src.core.database import AsyncSession, get_db
from src.core.security import get_current_user
from src.models.user import User
from src.models.project import Project
from src.schemas import (
    ProjectResponse,
    ProjectUpdateRequest,
    ErrorResponse,
)
from src.services import ProjectService


router = APIRouter(prefix="/api/v1/projects", tags=["Projects"])


@router.get(
    "",
    response_model=List[ProjectResponse],
    summary="Получить все проекты",
    description="Получить список всех проектов, принадлежащих текущему пользователю.",
    responses={
        200: {"description": "Проекты успешно получены."},
        401: {"model": ErrorResponse, "description": "Не подтверждено"},
    },
)
async def get_projects(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(session)
    projects = await service.get_projects(current_user)
    return projects


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Обновить проект",
    description="Обновите название проекта и/или значок.",
    responses={
        200: {"description": "Проект успешно обновлен."},
        401: {"model": ErrorResponse, "description": "Не подтверждено"},
        403: {"model": ErrorResponse, "description": "Доступ запрещен"},
        404: {"model": ErrorResponse, "description": "Проект не найден"},
    },
)
async def update_project(
    project_id: int,
    request: ProjectUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(session)
    project = await service.update_project(project_id, current_user, request)
    return project


@router.delete(
    "/{project_id}",
    summary="Удалить проект",
    description="Удалите проект и все его задачи.",
    responses={
        200: {"description": "Проект успешно удалён."},
        401: {"model": ErrorResponse, "description": "Не подтверждено"},
        403: {"model": ErrorResponse, "description": "Доступ запрещен"},
        404: {"model": ErrorResponse, "description": "Проект не найден"},
    },
)
async def delete_project(
    project_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(session)
    return await service.delete_project(project_id, current_user)
