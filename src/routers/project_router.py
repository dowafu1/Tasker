"""Project router."""

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
    summary="Get all projects",
    description="Get list of all projects owned by current user.",
    responses={
        200: {"description": "Projects retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def get_projects(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all user projects."""
    service = ProjectService(session)
    projects = await service.get_projects(current_user)
    return projects


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
    description="Update project name and/or icon.",
    responses={
        200: {"description": "Project updated successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Project not found"},
    },
)
async def update_project(
    project_id: int,
    request: ProjectUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update project."""
    service = ProjectService(session)
    project = await service.update_project(project_id, current_user, request)
    return project


@router.delete(
    "/{project_id}",
    summary="Delete project",
    description="Delete a project and all its tasks.",
    responses={
        200: {"description": "Project deleted successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Project not found"},
    },
)
async def delete_project(
    project_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete project."""
    service = ProjectService(session)
    return await service.delete_project(project_id, current_user)
