from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

class PracticeRecord(Base):
    __tablename__ = "practice_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("review_schedules.id"), nullable=True)
    record_type = Column(String(20), nullable=False)  # 'practice' or 'review'
    user_answer = Column(Text, nullable=True)
    correct_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=False)
    partial_score = Column(Float, default=0.0)
    max_score = Column(Float, default=100.0)
    time_spent = Column(Integer, default=0)
    answer_details = Column(Text, nullable=True)
    practiced_at = Column(DateTime, server_default=func.now())

    # 关系
    user = relationship("User", back_populates="practice_records")
    question = relationship("Question", back_populates="practice_records")

    # 索引
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_question_id', 'question_id'),
        Index('idx_practiced_at', 'practiced_at'),
        Index('idx_is_correct', 'is_correct'),
        Index('idx_partial_score', 'partial_score'),
    )

    def __repr__(self):
        return f"<PracticeRecord(id={self.id}, user_id={self.user_id}, question_id={self.question_id})>"