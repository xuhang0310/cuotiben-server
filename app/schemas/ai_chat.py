from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# AI Chat Group Schemas
class AiChatGroupBase(BaseModel):
    name: str
    status: Optional[str] = "active"
    user_id: Optional[int] = None


class AiChatGroupCreate(AiChatGroupBase):
    pass


class AiChatGroupUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    user_id: Optional[int] = None


class AiChatGroupResponse(AiChatGroupBase):
    id: int
    created_at: datetime
    updated_at: datetime
    member_count: int = 0  # 新增成员数量字段

    class Config:
        from_attributes = True


# AI Group Member Schemas
class AiGroupMemberBase(BaseModel):
    group_id: int
    ai_model: str
    ai_nickname: str
    personality: str
    initial_stance: Optional[str] = None
    user_id: Optional[int] = None
    member_type: Optional[int] = None  # 0 for human, 1 for AI


class AiGroupMemberCreate(AiGroupMemberBase):
    pass


class AiGroupMemberUpdate(BaseModel):
    ai_model: Optional[str] = None
    ai_nickname: Optional[str] = None
    personality: Optional[str] = None
    initial_stance: Optional[str] = None
    user_id: Optional[int] = None
    member_type: Optional[int] = None


class AiGroupMemberResponse(AiGroupMemberBase):
    id: int
    created_at: datetime
    avatar: Optional[str] = None
    avatarColor: Optional[str] = None

    class Config:
        from_attributes = True


# AI Message Schemas
class AiMessageBase(BaseModel):
    group_id: int
    member_id: int
    content: str
    message_type: Optional[str] = "text"


class AiMessageCreate(AiMessageBase):
    pass


class AiMessageUpdate(BaseModel):
    content: Optional[str] = None
    message_type: Optional[str] = None


class AiMessageResponse(AiMessageBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# AI Model Schemas
from pydantic import field_validator

class AiModelBase(BaseModel):
    model_name: str
    description: Optional[str] = None
    api_key: str
    api_secret: Optional[str] = None
    endpoint: Optional[str] = None
    is_active: Optional[bool] = True

    class Config:
        from_attributes = True


class AiModelCreate(AiModelBase):
    pass


class AiModelUpdate(BaseModel):
    model_name: Optional[str] = None
    description: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    endpoint: Optional[str] = None
    is_active: Optional[bool] = None


class AiModelResponse(AiModelBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_validator('is_active', mode='before')
    @classmethod
    def convert_is_active(cls, v):
        # Convert integer back to boolean for response
        if isinstance(v, int):
            return bool(v)
        return v


# Pagination schemas
class PaginatedGroups(BaseModel):
    total: int
    page: int
    size: int
    pages: int
    data: List[AiChatGroupResponse]


class PaginatedMembers(BaseModel):
    total: int
    page: int
    size: int
    pages: int
    data: List[AiGroupMemberResponse]


class PaginatedMessages(BaseModel):
    total: int
    page: int
    size: int
    pages: int
    data: List[AiMessageResponse]


class PaginatedModels(BaseModel):
    total: int
    page: int
    size: int
    pages: int
    data: List[AiModelResponse]