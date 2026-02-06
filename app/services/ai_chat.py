from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import Optional, Tuple, List
from app.models.ai_chat import AiChatGroup, AiGroupMember, AiMessage, AiModel
from app.schemas.ai_chat import (
    AiChatGroupCreate, AiChatGroupUpdate,
    AiGroupMemberCreate, AiGroupMemberUpdate,
    AiMessageCreate, AiMessageUpdate,
    AiModelCreate, AiModelUpdate
)
import logging

logger = logging.getLogger(__name__)

# AI Chat Group Services
def get_ai_chat_group(db: Session, group_id: int):
    """根据ID获取群聊"""
    return db.query(AiChatGroup).filter(AiChatGroup.id == group_id).first()


def get_ai_chat_groups(db: Session, skip: int = 0, limit: int = 10, status: Optional[str] = None, user_id: Optional[int] = None):
    """获取群聊列表（支持分页、状态筛选和用户筛选）"""
    query = db.query(AiChatGroup)

    if status:
        query = query.filter(AiChatGroup.status == status)

    if user_id is not None:
        query = query.filter(AiChatGroup.user_id == user_id)
    logger.info(f"Querying AI chat groups with skip={skip}, limit={limit}, status={status}, user_id={user_id}")
    total = query.count()
    groups = query.order_by(desc(AiChatGroup.updated_at)).offset(skip).limit(limit).all()
    
    # 为每个群组添加成员数量
    from sqlalchemy import func
    enhanced_groups = []
    for group in groups:
        # 计算该群组的成员数量
        member_count = db.query(AiGroupMember).filter(AiGroupMember.group_id == group.id).count()
        # 手动添加成员数量属性
        group.member_count = member_count
        enhanced_groups.append(group)
    
    return enhanced_groups, total


def create_ai_chat_group(db: Session, group: AiChatGroupCreate):
    """创建新群聊"""
    db_group = AiChatGroup(**group.model_dump())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    # 自动将创建者添加为群组成员
    if group.user_id is not None:
        member_data = AiGroupMemberCreate(
            group_id=db_group.id,
            user_id=group.user_id,
            ai_model="",  # 对于人类用户不需要AI模型
            ai_nickname="",  # 对于人类用户不需要AI昵称
            personality="",  # 对于人类用户不需要个性设置
            initial_stance="",  # 对于人类用户不需要初始立场
            member_type=0  # 0表示人类用户
        )
        create_ai_group_member(db, member_data)
    
    return db_group


def update_ai_chat_group(db: Session, group_id: int, group_update: AiChatGroupUpdate):
    """更新群聊信息"""
    db_group = db.query(AiChatGroup).filter(AiChatGroup.id == group_id).first()
    if db_group:
        update_data = group_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_group, field, value)
        db.commit()
        db.refresh(db_group)
    return db_group


def delete_ai_chat_group(db: Session, group_id: int):
    """删除群聊"""
    db_group = db.query(AiChatGroup).filter(AiChatGroup.id == group_id).first()
    if db_group:
        db.delete(db_group)
        db.commit()
    return db_group


# AI Group Member Services
def get_ai_group_member(db: Session, member_id: int):
    """根据ID获取群成员"""
    return db.query(AiGroupMember).filter(AiGroupMember.id == member_id).first()


def get_ai_group_members(db: Session, group_id: int, skip: int = 0, limit: int = 10, member_type: Optional[int] = None):
    """获取群成员列表（支持分页和成员类型筛选）"""
    from app.api.ai_chat import get_personality_info
    
    query = db.query(AiGroupMember).filter(AiGroupMember.group_id == group_id)

    if member_type is not None:
        query = query.filter(AiGroupMember.member_type == member_type)

    total = query.count()
    raw_members = query.offset(skip).limit(limit).all()
    
    # 处理成员数据，添加avatar和avatarColor字段
    processed_members = []
    for member in raw_members:
        # 创建一个字典副本
        member_dict = member.__dict__.copy()
        
        # 移除SQLAlchemy内部属性
        member_dict.pop('_sa_instance_state', None)
        
        # 计算avatar（昵称第一个字符）
        nickname = member.ai_nickname or str(member.id)  # 如果没有昵称，使用ID
        avatar = nickname[0].upper() if nickname else None
        
        # 计算avatarColor（根据personality获取颜色）
        _, avatar_color = get_personality_info(member.personality)
        
        # 添加新的字段
        member_dict['avatar'] = avatar
        member_dict['avatarColor'] = avatar_color
        
        # 创建响应对象
        from app.schemas.ai_chat import AiGroupMemberResponse
        processed_member = AiGroupMemberResponse(**member_dict)
        processed_members.append(processed_member)
    
    return processed_members, total


def create_ai_group_member(db: Session, member: AiGroupMemberCreate):
    """添加群成员"""
    db_member = AiGroupMember(**member.model_dump())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


def update_ai_group_member(db: Session, member_id: int, member_update: AiGroupMemberUpdate):
    """更新群成员信息"""
    db_member = db.query(AiGroupMember).filter(AiGroupMember.id == member_id).first()
    if db_member:
        update_data = member_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_member, field, value)
        db.commit()
        db.refresh(db_member)
    return db_member


def delete_ai_group_member(db: Session, member_id: int):
    """删除群成员"""
    db_member = db.query(AiGroupMember).filter(AiGroupMember.id == member_id).first()
    if db_member:
        db.delete(db_member)
        db.commit()
    return db_member


# AI Message Services
def get_ai_message(db: Session, message_id: int):
    """根据ID获取消息"""
    return db.query(AiMessage).filter(AiMessage.id == message_id).first()


def get_ai_messages(db: Session, group_id: int, skip: int = 0, limit: int = 10):
    """获取群聊消息列表（支持分页）"""
    query = db.query(AiMessage).filter(AiMessage.group_id == group_id)
    total = query.count()
    messages = query.order_by(AiMessage.created_at).offset(skip).limit(limit).all()
    return messages, total


def create_ai_message(db: Session, message: AiMessageCreate):
    """创建新消息"""
    db_message = AiMessage(**message.model_dump())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def update_ai_message(db: Session, message_id: int, message_update: AiMessageUpdate):
    """更新消息信息"""
    db_message = db.query(AiMessage).filter(AiMessage.id == message_id).first()
    if db_message:
        update_data = message_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_message, field, value)
        db.commit()
        db.refresh(db_message)
    return db_message


def delete_ai_message(db: Session, message_id: int):
    """删除消息"""
    db_message = db.query(AiMessage).filter(AiMessage.id == message_id).first()
    if db_message:
        db.delete(db_message)
        db.commit()
    return db_message


# AI Model Services
def get_ai_model(db: Session, model_id: int):
    """根据ID获取AI模型"""
    model = db.query(AiModel).filter(AiModel.id == model_id).first()
    if model:
        # Convert is_active integer back to boolean for response
        model.is_active = bool(model.is_active)
    return model


def get_ai_models(db: Session, skip: int = 0, limit: int = 10, is_active: Optional[bool] = None):
    """获取AI模型列表（支持分页和激活状态筛选）"""
    query = db.query(AiModel)

    if is_active is not None:
        # Convert boolean to integer for MySQL compatibility (1 for True, 0 for False)
        query = query.filter(AiModel.is_active == (1 if is_active else 0))

    total = query.count()
    models = query.order_by(desc(AiModel.updated_at)).offset(skip).limit(limit).all()

    # Convert is_active integers back to booleans for response
    for model in models:
        model.is_active = bool(model.is_active)

    return models, total


def create_ai_model(db: Session, model: AiModelCreate):
    """创建新AI模型"""
    # Convert boolean to integer for MySQL compatibility
    model_data = model.model_dump()
    # Convert boolean to integer for MySQL compatibility (1 for True, 0 for False)
    model_data['is_active'] = 1 if model_data.get('is_active', True) else 0

    db_model = AiModel(**model_data)
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model


def update_ai_model(db: Session, model_id: int, model_update: AiModelUpdate):
    """更新AI模型信息"""
    db_model = db.query(AiModel).filter(AiModel.id == model_id).first()
    if db_model:
        update_data = model_update.model_dump(exclude_unset=True)

        # Convert boolean to integer for MySQL compatibility (1 for True, 0 for False)
        if 'is_active' in update_data:
            update_data['is_active'] = 1 if update_data['is_active'] else 0

        for field, value in update_data.items():
            setattr(db_model, field, value)
        db.commit()
        db.refresh(db_model)
    return db_model


def delete_ai_model(db: Session, model_id: int):
    """删除AI模型"""
    db_model = db.query(AiModel).filter(AiModel.id == model_id).first()
    if db_model:
        db.delete(db_model)
        db.commit()
    return db_model