from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProjectBase(BaseModel):
    name: str
    icon: Optional[str] = None
    category_id: Optional[int] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    category_id: Optional[int] = None

class ProjectResponse(ProjectBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True