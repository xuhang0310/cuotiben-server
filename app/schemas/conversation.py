from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class ConversationBase(BaseModel):
    id: str
    conversation_type: Optional[str] = "private"
    conversation_name: Optional[str] = None
    avatar: Optional[str] = None
    description: Optional[str] = None


class ConversationCreate(BaseModel):
    id: str
    conversation_type: Optional[str] = "private"
    conversation_name: Optional[str] = None
    avatar: Optional[str] = None
    description: Optional[str] = None


class ConversationUpdate(BaseModel):
    conversation_type: Optional[str] = None
    conversation_name: Optional[str] = None
    avatar: Optional[str] = None
    description: Optional[str] = None


class ConversationResponse(ConversationBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationMemberBase(BaseModel):
    conversation_id: str
    user_id: int
    user_role: Optional[str] = "member"


class ConversationMemberCreate(BaseModel):
    conversation_id: str
    user_id: int
    user_role: Optional[str] = "member"


class ConversationMemberUpdate(BaseModel):
    user_role: Optional[str] = None


class ConversationMemberResponse(ConversationMemberBase):
    id: int
    joined_at: datetime

    class Config:
        from_attributes = True


class ConversationMemberWithUserInfo(BaseModel):
    conversation_id: str
    user_id: int
    user_role: Optional[str] = "member"
    id: int
    joined_at: datetime
    member_name: Optional[str] = None
    avatar: Optional[str] = None

    class Config:
        from_attributes = True


class ChatMessageBase(BaseModel):
    conversation_id: str
    user_id: int
    content: Optional[str] = None
    message_type: Optional[str] = "text"
    content_format: Optional[str] = "plain"
    is_deleted: Optional[int] = 0
    message_metadata: Optional[Dict[str, Any]] = None
    display_time: Optional[str] = None


class ChatMessageCreate(BaseModel):
    conversation_id: str
    user_id: int
    content: Optional[str] = None
    message_type: Optional[str] = "text"
    content_format: Optional[str] = "plain"
    message_metadata: Optional[Dict[str, Any]] = None
    display_time: Optional[str] = None


class ChatMessageUpdate(BaseModel):
    content: Optional[str] = None
    message_type: Optional[str] = None
    content_format: Optional[str] = None
    is_deleted: Optional[int] = None
    message_metadata: Optional[Dict[str, Any]] = None
    display_time: Optional[str] = None


class ChatMessageResponse(ChatMessageBase):
    id: int
    created_at: datetime
    updated_at: datetime
    member_name: Optional[str] = None
    avatar: Optional[str] = None

    class Config:
        from_attributes = True


class PaginatedConversations(BaseModel):
    total: int
    page: int
    size: int
    pages: int
    data: List[ConversationResponse]


class PaginatedMessages(BaseModel):
    total: int
    page: int
    size: int
    pages: int
    data: List[ChatMessageResponse]


class PaginatedMembers(BaseModel):
    total: int
    page: int
    size: int
    pages: int
    data: List[ConversationMemberWithUserInfo]