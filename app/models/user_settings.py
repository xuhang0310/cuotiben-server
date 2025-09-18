from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    study_goal = Column(Integer, default=10)
    preferred_subjects = Column(Text, nullable=True)  # JSON格式存储
    difficulty = Column(String(10), default="medium")  # 'easy', 'medium', 'hard'
    theme = Column(String(10), default="light")  # 'light', 'dark', 'auto'
    language = Column(String(10), default="zh-CN")
    font_size = Column(String(10), default="medium")  # 'small', 'medium', 'large'
    enable_notifications = Column(Boolean, default=True)
    study_reminder = Column(Boolean, default=True)
    reminder_time = Column(String(8), default="20:00:00")  # HH:MM:SS格式
    auto_backup = Column(Boolean, default=True)
    backup_frequency = Column(String(10), default="daily")  # 'daily', 'weekly', 'monthly'
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="settings")

    # 索引
    __table_args__ = (
        Index('uk_user_settings', 'user_id', unique=True),
    )

    def __repr__(self):
        return f"<UserSettings(id={self.id}, user_id={self.user_id})>"