from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import Optional, Tuple, List
from app.models.conversation import Conversation, ConversationMember, ChatMessage
from app.models.historical_figure import HistoricalFigure
from app.schemas.conversation import (
    ConversationCreate, ConversationUpdate,
    ConversationMemberCreate, ConversationMemberUpdate,
    ChatMessageCreate, ChatMessageUpdate
)


# 会话相关服务
def get_conversation(db: Session, conversation_id: str):
    """根据ID获取会话"""
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()


def get_conversations(db: Session, skip: int = 0, limit: int = 10, conversation_type: Optional[str] = None):
    """获取会话列表（支持分页和类型筛选）"""
    query = db.query(Conversation)
    
    if conversation_type:
        query = query.filter(Conversation.conversation_type == conversation_type)
    
    total = query.count()
    conversations = query.order_by(desc(Conversation.updated_at)).offset(skip).limit(limit).all()
    return conversations, total


def create_conversation(db: Session, conversation: ConversationCreate):
    """创建新会话"""
    db_conversation = Conversation(**conversation.model_dump())
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation


def update_conversation(db: Session, conversation_id: str, conversation_update: ConversationUpdate):
    """更新会话信息"""
    db_conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if db_conversation:
        update_data = conversation_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_conversation, field, value)
        db.commit()
        db.refresh(db_conversation)
    return db_conversation


def delete_conversation(db: Session, conversation_id: str):
    """删除会话"""
    db_conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if db_conversation:
        db.delete(db_conversation)
        db.commit()
    return db_conversation


# 会话成员相关服务
def get_conversation_member(db: Session, member_id: int):
    """根据ID获取会话成员"""
    return db.query(ConversationMember).filter(ConversationMember.id == member_id).first()


def get_conversation_members(db: Session, conversation_id: str, skip: int = 0, limit: int = 10):
    """获取会话成员列表（支持分页）"""
    # 使用JOIN查询获取成员的名称和头像信息
    query = db.query(
        ConversationMember,
        HistoricalFigure.name.label('member_name'),
        HistoricalFigure.avatar.label('avatar')
    ).outerjoin(
        HistoricalFigure, ConversationMember.user_id == HistoricalFigure.id
    ).filter(ConversationMember.conversation_id == conversation_id)

    total_query = db.query(ConversationMember).filter(ConversationMember.conversation_id == conversation_id)
    total = total_query.count()

    results = query.offset(skip).limit(limit).all()
    # 将结果转换为包含额外字段的对象
    from app.schemas.conversation import ConversationMemberWithUserInfo
    members = []
    for member, member_name, avatar in results:
        # 创建包含额外字段的响应对象
        member_response = ConversationMemberWithUserInfo(
            id=member.id,
            conversation_id=member.conversation_id,
            user_id=member.user_id,
            user_role=member.user_role,
            joined_at=member.joined_at,
            member_name=member_name,
            avatar=avatar
        )
        members.append(member_response)

    return members, total


def get_user_conversations(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    """获取用户参与的所有会话"""
    query = db.query(Conversation).join(ConversationMember).filter(ConversationMember.user_id == user_id)
    total = query.count()
    conversations = query.offset(skip).limit(limit).all()
    return conversations, total


def add_conversation_member(db: Session, member: ConversationMemberCreate):
    """添加会话成员"""
    db_member = ConversationMember(**member.model_dump())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


def update_conversation_member(db: Session, member_id: int, member_update: ConversationMemberUpdate):
    """更新会话成员信息"""
    db_member = db.query(ConversationMember).filter(ConversationMember.id == member_id).first()
    if db_member:
        update_data = member_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_member, field, value)
        db.commit()
        db.refresh(db_member)
    return db_member


def remove_conversation_member(db: Session, member_id: int):
    """移除会话成员"""
    db_member = db.query(ConversationMember).filter(ConversationMember.id == member_id).first()
    if db_member:
        db.delete(db_member)
        db.commit()
    return db_member


def remove_user_from_conversation(db: Session, conversation_id: str, user_id: int):
    """将用户从会话中移除"""
    db_member = db.query(ConversationMember).filter(
        and_(ConversationMember.conversation_id == conversation_id, 
             ConversationMember.user_id == user_id)
    ).first()
    if db_member:
        db.delete(db_member)
        db.commit()
    return db_member


# 消息相关服务
def get_chat_message(db: Session, message_id: int):
    """根据ID获取聊天消息"""
    return db.query(ChatMessage).filter(ChatMessage.id == message_id).first()


def get_chat_messages(db: Session, conversation_id: str, skip: int = 0, limit: int = 10):
    """获取会话中的消息列表（支持分页）"""
    query = db.query(ChatMessage).filter(
        and_(ChatMessage.conversation_id == conversation_id, 
             ChatMessage.is_deleted == 0)  # 只返回未删除的消息
    )
    total = query.count()
    messages = query.order_by(ChatMessage.created_at).offset(skip).limit(limit).all()
    return messages, total


def create_chat_message(db: Session, message: ChatMessageCreate):
    """创建新消息"""
    # 将message_metadata映射到数据库列名metadata
    message_dict = message.model_dump()
    # 由于模型中使用了Column('metadata', ...)，SQLAlchemy会自动映射
    db_message = ChatMessage(**message_dict)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def update_chat_message(db: Session, message_id: int, message_update: ChatMessageUpdate):
    """更新消息信息"""
    db_message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
    if db_message:
        update_data = message_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_message, field, value)
        db.commit()
        db.refresh(db_message)
    return db_message


def delete_chat_message(db: Session, message_id: int):
    """删除消息（软删除）"""
    db_message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
    if db_message:
        db_message.is_deleted = 1
        db.commit()
        db.refresh(db_message)
    return db_message


def get_user_messages(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    """获取用户发送的所有消息"""
    query = db.query(ChatMessage).filter(ChatMessage.user_id == user_id)
    total = query.count()
    messages = query.order_by(desc(ChatMessage.created_at)).offset(skip).limit(limit).all()
    return messages, total