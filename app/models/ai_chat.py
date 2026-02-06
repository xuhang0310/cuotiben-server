from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Enum, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import and_
from app.database.session import Base
from typing import Optional


class AiChatGroup(Base):
    __tablename__ = "ai_chat_groups"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment='群聊名称')
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    status = Column(Enum('active', 'inactive', name='group_status_enum'), default='active', comment='群聊状态')
    user_id = Column(Integer, nullable=True, comment='创建人id')


class AiGroupMember(Base):
    __tablename__ = "ai_group_members"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    group_id = Column(Integer, nullable=False, comment='群聊ID')
    ai_model = Column(String(100), nullable=False, comment='底层AI模型')
    ai_nickname = Column(String(100), nullable=False, comment='AI昵称，当member_type=0的时候 ，从users中取值；')
    personality = Column(String(255), nullable=False, comment='个性设置')
    initial_stance = Column(Text, comment='初始立场')
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    user_id = Column(Integer, nullable=True, comment='当member_type=1的时候 ，从ai_models中取值；')
    member_type = Column(Integer, nullable=True, comment='0 人  1 AI')


class AiMessage(Base):
    __tablename__ = "ai_messages"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    group_id = Column(Integer, nullable=False, comment='群聊ID')
    member_id = Column(Integer, nullable=False, comment='发送者成员ID')
    content = Column(Text, nullable=False, comment='消息内容')
    message_type = Column(Enum('text', 'image', 'file', name='message_type_enum'), default='text', comment='消息类型')
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    


class AiModel(Base):
    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_name = Column(String(100), unique=True, nullable=False, comment='模型名称')
    description = Column(Text, comment='模型描述')
    api_key = Column(String(255), nullable=False, comment='API密钥')
    api_secret = Column(String(255), comment='API密钥（可选）')
    endpoint = Column(String(255), comment='API端点')
    is_active = Column(Integer, default=1, comment='是否启用')  # Using Integer instead of Boolean for MySQL compatibility
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())