from repositories.project import ProjectRepository
from schemas.project import ProjectCreate, ProjectUpdate

class ProjectService:
    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo

    async def get_projects(self, user_id: int):
        return await self.project_repo.get_by_user(user_id)

    async def create_project(self, user_id: int, data: ProjectCreate):
        return await self.project_repo.create(user_id=user_id, **data.dict())

    async def update_project(self, project_id: int, data: ProjectUpdate):
        return await self.project_repo.update(project_id, **data.dict(exclude_unset=True))

    async def delete_project(self, project_id: int):
        return await self.project_repo.delete(project_id)