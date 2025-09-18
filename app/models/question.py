from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    question_type_id = Column(Integer, ForeignKey("question_types.id"), nullable=False)
    difficulty = Column(Enum("easy", "medium", "hard"), nullable=False, default="medium")
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    explanation = Column(Text, nullable=True)
    correct_answer = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    is_favorite = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="questions")
    subject = relationship("Subject", back_populates="questions")
    question_type = relationship("QuestionType", back_populates="questions")
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="question_tags", back_populates="questions")
    practice_records = relationship("PracticeRecord", back_populates="question", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_subject_difficulty', 'subject_id', 'difficulty'),
        Index('idx_created_at', 'created_at'),
        Index('idx_is_favorite', 'is_favorite'),
    )

    def __repr__(self):
        return f"<Question(id={self.id}, title='{self.title}', user_id={self.user_id})>"