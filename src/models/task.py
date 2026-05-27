"""Модели для тасков и категорий"""

from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from enum import Enum as PyEnum

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Integer,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.core.database import Base


if TYPE_CHECKING:
    from .user import User
    from .project import Project


class ImportanceLevel(str, PyEnum):
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    
    @property
    def emoji(self) -> str:
        mapping = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
        }
        return mapping.get(self.value, "⚪")


class TaskStatus(str, PyEnum):
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Category(Base):
    
    __tablename__ = "categories"
    
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    color: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        default="#808080",
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="category",
    )
    user: Mapped["User"] = relationship(
        "User",
        backref="categories",
    )
    
    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name})>"


class Task(Base):
    
    __tablename__ = "tasks"
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
    )
    importance: Mapped[ImportanceLevel] = mapped_column(
        SQLEnum(ImportanceLevel),
        default=ImportanceLevel.MEDIUM,
        nullable=False,
    )
    deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )    
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assignee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    category: Mapped[Optional["Category"]] = relationship(
        "Category",
        back_populates="tasks",
    )
    project: Mapped[Optional["Project"]] = relationship(
        "Project",
        back_populates="tasks",
    )
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by_id],
        back_populates="created_tasks",
    )
    assignee: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assignee_id],
        back_populates="assigned_tasks",
    )
    
    @validates("name")
    def validate_name(self, key: str, value: str) -> str:
        if not value or len(value.strip()) == 0:
            raise ValueError("Task name cannot be empty")
        return value.strip()
    
    def mark_completed(self) -> None:
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
    
    def __repr__(self) -> str:
        return f"<Task(id={self.id}, name={self.name}, status={self.status.value})>"
