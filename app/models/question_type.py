from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

class QuestionType(Base):
    __tablename__ = "question_types"

    id = Column(Integer, primary_key=True, index=True)
    type_name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    questions = relationship("Question", back_populates="question_type")

    def __repr__(self):
        return f"<QuestionType(id={self.id}, type_name='{self.type_name}')>"