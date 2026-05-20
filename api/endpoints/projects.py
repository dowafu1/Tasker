from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.deps import get_current_user, get_db
from models.user import User
from schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from services.project import ProjectService
from repositories.project import ProjectRepository

router = APIRouter()

@router.get("/", response_model=list[ProjectResponse])
async def get_projects(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = ProjectService(ProjectRepository(db))
    return await service.get_projects(current_user.id)

@router.post("/", response_model=ProjectResponse)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = ProjectService(ProjectRepository(db))
    return await service.create_project(current_user.id, data)

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, data: ProjectUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = ProjectService(ProjectRepository(db))
    return await service.update_project(project_id, data)

@router.delete("/{project_id}")
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = ProjectService(ProjectRepository(db))
    await service.delete_project(project_id)
    return {"message": "Project deleted"}