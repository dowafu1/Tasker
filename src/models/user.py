"""SQLAlchemy модели"""

from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Text,
    Integer,
    Index,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    validates,
    declared_attr,
)
import re

from src.core.database import Base


if TYPE_CHECKING:
    from .task import Task
    from .project import Project
    from .category import Category

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9\-_.]+@[A-Za-z0-9\-_.]+\.[A-Za-z]{2,}$")
PASSWORD_PATTERN = re.compile(r"^[A-Za-z0-9!#$%&*+.<=>?@^_-]{8,16}$")
NAME_PATTERN = re.compile(r"^[А-Яа-яA-Za-z\- ]{1,50}$")


class User(Base):
        
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    avatar_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
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
    created_tasks: Mapped[List["Task"]] = relationship(
        "Task",
        foreign_keys="Task.created_by_id",
        back_populates="creator",
    )
    assigned_tasks: Mapped[List["Task"]] = relationship(
        "Task",
        foreign_keys="Task.assignee_id",
        back_populates="assignee",
    )
    projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    
    @validates("email")
    def validate_email(self, key: str, value: str) -> str:
        if not EMAIL_PATTERN.match(value):
            raise ValueError("Неверный формат почты")
        return value.lower()
    
    @validates("name")
    def validate_name(self, key: str, value: Optional[str]) -> Optional[str]:
        if value is not None and not NAME_PATTERN.match(value):
            raise ValueError("Недопустимый формат имени")
        return value
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"

Index("ix_users_email_is_active", "users", "email", "is_active")


class RefreshToken(Base):
        
    __tablename__ = "refresh_tokens"
    
    token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    user: Mapped["User"] = relationship(
        "User",
        backref="refresh_tokens",
    )
    
    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id})>"


class PasswordResetCode(Base):
    
    __tablename__ = "password_reset_codes"
    
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(
        String(6),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    def __repr__(self) -> str:
        return f"<PasswordResetCode(email={self.email}, code={self.code})>"