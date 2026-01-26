from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database.session import Base


class HistoricalFigure(Base):
    """
    历史人物模型
    """
    __tablename__ = "historical_figures"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)  # 人物姓名
    avatar = Column(String(255), nullable=True)  # 头像路径
    role = Column(String(100), nullable=True)  # 角色/头衔
    status = Column(String(20), nullable=True)  # 状态 (online/offline)
    create_time = Column(String(50), nullable=True)  # 创建时间（可为历史时间）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())