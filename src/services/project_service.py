"""Бизнес логика проектов."""

import logging
from typing import List

from fastapi import HTTPException, status

from src.repositories import (
    ProjectRepository,
)
from src.models.user import User
from src.models.project import Project
from src.schemas import (
    ProjectUpdateRequest,
)


logger = logging.getLogger(__name__)


class ProjectService:
    
    def __init__(self, session):
        self.session = session
        self.project_repo = ProjectRepository(session)
    
    async def get_projects(self, user: User) -> List[Project]:
        return await self.project_repo.get_user_projects(user.id)
    
    async def get_project(self, project_id: int, user: User) -> Project:
        project = await self.project_repo.get_by_id(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Проект не найден",
            )
        
        if project.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ к проекту запрещен",
            )
        
        return project
    
    async def update_project(
        self,
        project_id: int,
        user: User,
        data: ProjectUpdateRequest,
    ) -> Project:
        project = await self.get_project(project_id, user)
        
        update_data = {}
        if data.name is not None:
            update_data["name"] = data.name
        if data.icon is not None:
            update_data["icon"] = data.icon
        
        if update_data:
            await self.project_repo.update(project, **update_data)
        
        return project
    
    async def delete_project(self, project_id: int, user: User) -> dict:
        project = await self.get_project(project_id, user)
        
        await self.project_repo.delete(project)
        
        return {"detail": "Проект успешно удален"}
