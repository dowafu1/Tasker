from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from db.session import Base
import enum

class PriorityEnum(str, enum.Enum):
    VERY_HIGH = "very_high"
    HIGH = "high"
    CAN_WAIT = "can_wait"
    LOW = "low"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    parent_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    priority = Column(Enum(PriorityEnum), nullable=False)
    due_date = Column(Date, nullable=False)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())