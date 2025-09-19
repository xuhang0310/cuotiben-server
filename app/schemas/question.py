from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        ),
        populate_by_name = True
    )

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

    model_config = ConfigDict(
        from_attributes=True,
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        ),
        populate_by_name = True
    )

# 题目列表数据模型
class QuestionListData(BaseModel):
    questions: List[Question]
    total: int
    page: int
    page_size: int
    
    model_config = ConfigDict(
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        )
    )

# 题目列表响应模型
class QuestionListResponse(BaseModel):
    data: QuestionListData

    model_config = ConfigDict(
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        )
    )

# 题目详情数据模型
class QuestionDetailData(BaseModel):
    question: Question
    related_questions: List[Question]
    
    model_config = ConfigDict(
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        )
    )

# 题目详情响应模型
class QuestionDetailResponse(BaseModel):
    data: QuestionDetailData

    model_config = ConfigDict(
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        )
    )

# 收藏状态切换数据模型
class FavoriteToggleData(BaseModel):
    is_favorite: bool
    
    model_config = ConfigDict(
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        )
    )

# 收藏状态切换响应模型
class FavoriteToggleResponse(BaseModel):
    data: FavoriteToggleData

    model_config = ConfigDict(
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        )
    )

# 题目创建数据模型
class QuestionCreateData(BaseModel):
    question: Question
    
    model_config = ConfigDict(
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        )
    )

# 题目创建响应模型
class QuestionCreateResponse(BaseModel):
    data: QuestionCreateData

    model_config = ConfigDict(
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        )
    )

# 题目更新数据模型
class QuestionUpdateData(BaseModel):
    question: Question
    
    model_config = ConfigDict(
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        )
    )

# 题目更新响应模型
class QuestionUpdateResponse(BaseModel):
    data: QuestionUpdateData

    model_config = ConfigDict(
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        )
    )

# 题目删除数据模型
class QuestionDeleteData(BaseModel):
    success: bool
    message: str
    
    model_config = ConfigDict(
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        )
    )

# 题目删除响应模型
class QuestionDeleteResponse(BaseModel):
    data: QuestionDeleteData

    model_config = ConfigDict(
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        )
    )