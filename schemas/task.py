from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from models.task import PriorityEnum

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: PriorityEnum
    due_date: date
    assignee_id: int
    project_id: Optional[int] = None
    parent_id: Optional[int] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    due_date: Optional[date] = None
    assignee_id: Optional[int] = None
    project_id: Optional[int] = None
    parent_id: Optional[int] = None

class TaskResponse(TaskBase):
    id: int
    author_id: int
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class TaskAssignedResponse(BaseModel):
    id: int
    title: str
    description_preview: Optional[str] = None
    priority: PriorityEnum
    author_name: Optional[str] = None  # имя автора или email

    class Config:
        orm_mode = True

class TaskComplete(BaseModel):
    is_completed: bool