from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database.session import Base

class QuestionTag(Base):
    __tablename__ = "question_tags"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # 复合唯一约束
    __table_args__ = (
        # 在MySQL中可以使用UniqueConstraint，但在某些版本中可能需要在数据库层面定义
        # UniqueConstraint('question_id', 'tag_id', name='uk_question_tag'),
    )

    def __repr__(self):
        return f"<QuestionTag(id={self.id}, question_id={self.question_id}, tag_id={self.tag_id})>"