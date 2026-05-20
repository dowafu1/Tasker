from pydantic import BaseModel
from typing import Optional

class CategoryBase(BaseModel):
    name: str
    color: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int

    class Config:
        orm_mode = True