from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from db.session import Base

class PasswordReset(Base):
    __tablename__ = "password_resets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    code = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)