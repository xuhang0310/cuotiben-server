from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# 题目基础模型
class QuestionBase(BaseModel):
    title: str
    content: str
    question_type_id: int
    difficulty: str
    subject_id: int
    explanation: Optional[str] = None
    correct_answer: Optional[str] = None
    image_url: Optional[str] = None

# 题目创建模型
class QuestionCreate(QuestionBase):
    pass

# 题目更新模型
class QuestionUpdate(QuestionBase):
    is_favorite: Optional[bool] = None

# 题目数据库模型
class Question(QuestionBase):
    id: int
    user_id: int
    is_favorite: bool
    created_at: datetime
    updated_at: datetime
    options: List[str] = []
    tags: List[str] = []
    subject: str = ""
    practice_count: int = 0
    correct_count: int = 0
    last_practice_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 题目列表响应模型
class QuestionListResponse(BaseModel):
    questions: List[Question]
    total: int
    page: int
    page_size: int

# 题目详情响应模型
class QuestionDetailResponse(BaseModel):
    question: Question
    related_questions: List[Question]

# 收藏状态切换响应模型
class FavoriteToggleResponse(BaseModel):
    is_favorite: bool