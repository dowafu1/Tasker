"""Pydantic схема"""

from datetime import datetime, timezone
from typing import Optional, List, Annotated
from enum import Enum

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict,
    EmailStr,
)
import re

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9\-_.]+@[A-Za-z0-9\-_.]+\.[A-Za-z]{2,}$")
PASSWORD_PATTERN = re.compile(r"^[A-Za-z0-9!#$%&*+.<=>?@^_-]{8,16}$")
NAME_PATTERN = re.compile(r"^[А-Яа-яA-Za-z\- ]{1,50}$")


class ImportanceLevel(str, Enum):
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# AUTH SCHEMAS

class RegisterRequest(BaseModel):
    
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=16)
    password_confirm: str
    accept_terms: bool
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not PASSWORD_PATTERN.match(v):
            raise ValueError(
                "Пароль должен быть от 8-16 символов и содержать: "
                "A-Za-z0-9!#$%&*+.<=>?@^_-"
            )
        return v
    
    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterRequest":
        if self.password != self.password_confirm:
            raise ValueError("Пароль не совпал")
        return self
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not EMAIL_PATTERN.match(v):
            raise ValueError("Не верный формат email")
        return v.lower()


class LoginRequest(BaseModel):
    
    email: EmailStr
    password: str
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not EMAIL_PATTERN.match(v):
            raise ValueError("Invalid email format")
        return v.lower()


class TokenResponse(BaseModel):
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    
    email: EmailStr
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not EMAIL_PATTERN.match(v):
            raise ValueError("Не верный формат email")
        return v.lower()


class VerifyCodeRequest(BaseModel):
    
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not EMAIL_PATTERN.match(v):
            raise ValueError("Не верный формат email")
        return v.lower()


class ResetPasswordRequest(BaseModel):
    
    email: EmailStr
    new_password: str = Field(..., min_length=8, max_length=16)
    password_confirm: str
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not PASSWORD_PATTERN.match(v):
            raise ValueError(
                "Пароль должен быть от 8-16 символов и содержать: "
                "A-Za-z0-9!#$%&*+.<=>?@^_-"
            )
        return v
    
    @model_validator(mode="after")
    def passwords_match(self) -> "ResetPasswordRequest":
        if self.new_password != self.password_confirm:
            raise ValueError("Пароль не совпал")
        return self
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not EMAIL_PATTERN.match(v):
            raise ValueError("Не верный формат почты")
        return v.lower()


# PROFILE SCHEMAS

class ProfileResponse(BaseModel):
    
    id: int
    email: str
    name: Optional[str] = None
    avatar_path: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ProfileUpdateRequest(BaseModel):
    
    name: Optional[Annotated[str, Field(max_length=50)]] = None
    email: Optional[EmailStr] = None
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not NAME_PATTERN.match(v):
            raise ValueError(
                "Не верный формат имени"
            )
        return v
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not EMAIL_PATTERN.match(v):
            raise ValueError("Не верный формат почты")
        return v.lower() if v else v


class ChangePasswordRequest(BaseModel):
    
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=16)
    password_confirm: str
    
    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if not PASSWORD_PATTERN.match(v):
            raise ValueError(
                "Пароль должен быть от 8-16 символов и содержать: "
                "A-Za-z0-9!#$%&*+.<=>?@^_-"
            )
        return v
    
    @model_validator(mode="after")
    def passwords_match(self) -> "ChangePasswordRequest":
        if self.new_password != self.password_confirm:
            raise ValueError("Пароль не совпал")
        return self


# PROJECT SCHEMAS

class ProjectResponse(BaseModel):

    id: int
    name: str
    icon: Optional[str] = None
    description: Optional[str] = None
    owner_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ProjectCreateRequest(BaseModel):
    
    name: str = Field(..., min_length=1, max_length=100)
    icon: Optional[str] = None
    description: Optional[str] = None


class ProjectUpdateRequest(BaseModel):
    
    name: Optional[Annotated[str, Field(min_length=1, max_length=100)]] = None
    icon: Optional[str] = None


# TASK SCHEMAS

class CategoryResponse(BaseModel):
    
    id: int
    name: str
    color: str
    user_id: int
    
    model_config = ConfigDict(from_attributes=True)


class TaskResponse(BaseModel):
    
    id: int
    name: str
    description: Optional[str] = None
    status: TaskStatus
    importance: ImportanceLevel
    deadline: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    category_id: Optional[int] = None
    project_id: Optional[int] = None
    created_by_id: int
    assignee_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    project_name: Optional[str] = None
    category_marker: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class TaskListItem(BaseModel):
    
    id: int
    name: str
    status: TaskStatus
    importance: ImportanceLevel
    deadline: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class AssignedTasksResponse(BaseModel):
    
    total: int
    completed: int
    tasks: List[TaskListItem]
    page: int
    page_size: int
    total_pages: int


class TaskFilterReset(BaseModel):
    pass


class CreateTaskRequest(BaseModel):
    
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category_id: Optional[int] = None
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None
    deadline: Optional[datetime] = None
    importance: ImportanceLevel = ImportanceLevel.MEDIUM


class CalendarDateMark(BaseModel):
    
    date: str
    task_count: int
    has_important: bool = False


class CalendarMonthResponse(BaseModel):
    
    year: int
    month: int
    dates: List[CalendarDateMark]


class CalendarDayTask(BaseModel):
    
    id: int
    name: str
    importance: ImportanceLevel
    status: TaskStatus
    deadline: Optional[datetime] = None


class CalendarDayTasksResponse(BaseModel):
    
    date: str
    tasks: List[CalendarDayTask]


# ERROR SCHEMAS

class ErrorResponse(BaseModel):
    
    detail: str
    code: str
