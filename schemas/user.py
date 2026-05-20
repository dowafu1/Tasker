from pydantic import BaseModel, EmailStr, constr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    email: EmailStr
    password: constr(min_length=8, max_length=16)
    confirm_password: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    email: Optional[EmailStr] = None

class ChangePassword(BaseModel):
    old_password: str
    new_password: constr(min_length=8, max_length=16)
    confirm_password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True