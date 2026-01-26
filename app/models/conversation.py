from sqlalchemy import Column, String, BigInteger, Integer, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.mysql import ENUM, JSON
from sqlalchemy.sql import func
from app.database.session import Base


class Conversation(Base):
    """
    会话表模型
    """
    __tablename__ = "conversations"

    id = Column(String(50), primary_key=True, comment='会话ID')
    conversation_type = Column(ENUM('private', 'group', 'channel'), default='private', comment='会话类型')
    conversation_name = Column(String(200), comment='会话名称（群聊时使用）')
    avatar = Column(String(255), comment='会话头像')
    description = Column(Text, comment='会话描述')
    created_at = Column(DateTime, server_default=func.current_timestamp(), comment='创建时间')
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment='更新时间')


class ConversationMember(Base):
    """
    会话成员表模型
    """
    __tablename__ = "conversation_members"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='成员关系ID')
    conversation_id = Column(String(50), ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, comment='会话ID')
    user_id = Column(BigInteger, nullable=False, comment='用户ID')
    user_role = Column(ENUM('owner', 'admin', 'member'), default='member', comment='用户角色')
    joined_at = Column(DateTime, server_default=func.current_timestamp(), comment='加入时间')

    __table_args__ = (
        UniqueConstraint('conversation_id', 'user_id', name='uk_conversation_user'),
    )


class ChatMessage(Base):
    """
    聊天消息表模型
    """
    __tablename__ = "chat_messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='消息ID')
    conversation_id = Column(String(50), ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, comment='会话ID，支持群聊和私聊')
    user_id = Column(BigInteger, nullable=False, comment='发送用户ID')
    content = Column(Text, comment='消息内容')
    message_type = Column(ENUM('text', 'emoji', 'image', 'voice', 'video', 'file', 'system'), default='text', comment='消息类型')
    content_format = Column(String(20), default='plain', comment='内容格式: plain/markdown/html')
    is_deleted = Column(Integer, default=0, comment='是否删除: 0-未删除, 1-已删除')
    message_metadata = Column('metadata', JSON, comment='扩展元数据，如图片尺寸、文件大小等')
    created_at = Column(DateTime, server_default=func.current_timestamp(), comment='创建时间')
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment='更新时间')
    display_time = Column(String(8), comment='消息显示时间')  # 使用String存储TIME类型