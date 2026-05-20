"""Pydantic schemas for DTOs and validation."""

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


# Validation patterns from TZ
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9\-_.]+@[A-Za-z0-9\-_.]+\.[A-Za-z]{2,}$")
PASSWORD_PATTERN = re.compile(r"^[A-Za-z0-9!#$%&*+.<=>?@^_-]{8,16}$")
NAME_PATTERN = re.compile(r"^[А-Яа-яA-Za-z\-]{1,50}$")


class ImportanceLevel(str, Enum):
    """Importance level for tasks."""
    
    CRITICAL = "critical"  # 🔴 очень срочно
    HIGH = "high"  # 🟠 срочно
    MEDIUM = "medium"  # 🟡 может подождать
    LOW = "low"  # 🟢 несрочно


class TaskStatus(str, Enum):
    """Task status."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ============================================================================
# AUTH SCHEMAS
# ============================================================================

class RegisterRequest(BaseModel):
    """Registration request schema."""
    
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=16)
    password_confirm: str
    accept_terms: bool
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password format."""
        if not PASSWORD_PATTERN.match(v):
            raise ValueError(
                "Password must be 8-16 characters and contain only: "
                "A-Za-z0-9!#$%&*+.<=>?@^_-"
            )
        return v
    
    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterRequest":
        """Check that passwords match."""
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if not EMAIL_PATTERN.match(v):
            raise ValueError("Invalid email format")
        return v.lower()


class LoginRequest(BaseModel):
    """Login request schema."""
    
    email: EmailStr
    password: str
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if not EMAIL_PATTERN.match(v):
            raise ValueError("Invalid email format")
        return v.lower()


class TokenResponse(BaseModel):
    """Token response schema."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    """Forgot password request schema."""
    
    email: EmailStr
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if not EMAIL_PATTERN.match(v):
            raise ValueError("Invalid email format")
        return v.lower()


class VerifyCodeRequest(BaseModel):
    """Verify code request schema."""
    
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if not EMAIL_PATTERN.match(v):
            raise ValueError("Invalid email format")
        return v.lower()


class ResetPasswordRequest(BaseModel):
    """Reset password request schema."""
    
    email: EmailStr
    new_password: str = Field(..., min_length=8, max_length=16)
    password_confirm: str
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password format."""
        if not PASSWORD_PATTERN.match(v):
            raise ValueError(
                "Password must be 8-16 characters and contain only: "
                "A-Za-z0-9!#$%&*+.<=>?@^_-"
            )
        return v
    
    @model_validator(mode="after")
    def passwords_match(self) -> "ResetPasswordRequest":
        """Check that passwords match."""
        if self.new_password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if not EMAIL_PATTERN.match(v):
            raise ValueError("Invalid email format")
        return v.lower()


# ============================================================================
# PROFILE SCHEMAS
# ============================================================================

class ProfileResponse(BaseModel):
    """Profile response schema."""
    
    id: int
    email: str
    name: Optional[str] = None
    avatar_path: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ProfileUpdateRequest(BaseModel):
    """Profile update request schema."""
    
    name: Optional[Annotated[str, Field(max_length=50)]] = None
    email: Optional[EmailStr] = None
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate name format."""
        if v is not None and not NAME_PATTERN.match(v):
            raise ValueError(
                "Invalid name format. Allowed: Cyrillic, Latin letters and hyphen, 1-50 chars."
            )
        return v
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format."""
        if v is not None and not EMAIL_PATTERN.match(v):
            raise ValueError("Invalid email format")
        return v.lower() if v else v


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""
    
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=16)
    password_confirm: str
    
    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password format."""
        if not PASSWORD_PATTERN.match(v):
            raise ValueError(
                "Password must be 8-16 characters and contain only: "
                "A-Za-z0-9!#$%&*+.<=>?@^_-"
            )
        return v
    
    @model_validator(mode="after")
    def passwords_match(self) -> "ChangePasswordRequest":
        """Check that passwords match."""
        if self.new_password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self


# ============================================================================
# PROJECT SCHEMAS
# ============================================================================

class ProjectResponse(BaseModel):
    """Project response schema."""
    
    id: int
    name: str
    icon: Optional[str] = None
    description: Optional[str] = None
    owner_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ProjectCreateRequest(BaseModel):
    """Project create request schema."""
    
    name: str = Field(..., min_length=1, max_length=100)
    icon: Optional[str] = None
    description: Optional[str] = None


class ProjectUpdateRequest(BaseModel):
    """Project update request schema."""
    
    name: Optional[Annotated[str, Field(min_length=1, max_length=100)]] = None
    icon: Optional[str] = None


# ============================================================================
# TASK SCHEMAS
# ============================================================================

class CategoryResponse(BaseModel):
    """Category response schema."""
    
    id: int
    name: str
    color: str
    user_id: int
    
    model_config = ConfigDict(from_attributes=True)


class TaskResponse(BaseModel):
    """Task response schema for full task details."""
    
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
    
    # Conditional fields based on context
    project_name: Optional[str] = None
    category_marker: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class TaskListItem(BaseModel):
    """Task list item schema."""
    
    id: int
    name: str
    status: TaskStatus
    importance: ImportanceLevel
    deadline: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class AssignedTasksResponse(BaseModel):
    """Assigned tasks response with counters."""
    
    total: int
    completed: int
    tasks: List[TaskListItem]
    page: int
    page_size: int
    total_pages: int


class TaskFilterReset(BaseModel):
    """Task filter reset request (empty body)."""
    pass


class CreateTaskRequest(BaseModel):
    """Create task request schema."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category_id: Optional[int] = None
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None
    deadline: Optional[datetime] = None
    importance: ImportanceLevel = ImportanceLevel.MEDIUM


class CalendarDateMark(BaseModel):
    """Calendar date mark with task count."""
    
    date: str  # ISO format date string
    task_count: int
    has_important: bool = False


class CalendarMonthResponse(BaseModel):
    """Calendar month response with date marks."""
    
    year: int
    month: int
    dates: List[CalendarDateMark]


class CalendarDayTask(BaseModel):
    """Task for calendar day view."""
    
    id: int
    name: str
    importance: ImportanceLevel
    status: TaskStatus
    deadline: Optional[datetime] = None


class CalendarDayTasksResponse(BaseModel):
    """Calendar day tasks response."""
    
    date: str
    tasks: List[CalendarDayTask]


# ============================================================================
# ERROR SCHEMAS
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response schema."""
    
    detail: str
    code: str  # VALIDATION_ERROR | AUTH_ERROR | NOT_FOUND | etc.
