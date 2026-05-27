"""Модели для проекта"""

from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


if TYPE_CHECKING:
    from .user import User
    from .task import Task

class Project(Base):
    
    __tablename__ = "projects"
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    icon: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default="?",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
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
    
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="projects",
    )
    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="project",
    )
    
    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name})>"
