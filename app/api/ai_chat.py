from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database.session import get_db
from app.schemas.ai_chat import (
    AiChatGroupCreate, AiChatGroupUpdate, AiChatGroupResponse,
    AiGroupMemberCreate, AiGroupMemberUpdate, AiGroupMemberResponse,
    AiMessageCreate, AiMessageUpdate, AiMessageResponse,
    AiModelCreate, AiModelUpdate, AiModelResponse,
    PaginatedGroups, PaginatedMembers, PaginatedMessages, PaginatedModels
)
from app.services.ai_chat import (
    get_ai_chat_group, get_ai_chat_groups, create_ai_chat_group, update_ai_chat_group, delete_ai_chat_group,
    get_ai_group_member, get_ai_group_members, create_ai_group_member, update_ai_group_member, delete_ai_group_member,
    get_ai_message, get_ai_messages, create_ai_message, update_ai_message, delete_ai_message,
    get_ai_model, get_ai_models, create_ai_model, update_ai_model, delete_ai_model
)
from app.core.middleware import JWTBearer
from app.schemas.user import TokenData
from app.services.user import get_current_user
import logging
logger = logging.getLogger(__name__)

# JWT authentication
oauth2_scheme = JWTBearer()

def get_personality_info(personality_value: str) -> tuple:
    """
    根据个性值获取对应的中文标签和颜色
    返回 (label, color) 元组
    """
    personality_options = [
            {
                "label": "严谨 (Rigorous)",
                "value": "rigorous",
                "color": "#4caf50",
                "description": "象征精确、平衡与可靠性"
            },
            {
                "label": "创意 (Creative)",
                "value": "creative",
                "color": "#9c27b0",
                "description": "代表想象力、灵感与艺术性"
            },
            {
                "label": "结构化 (Structured)",
                "value": "structured",
                "color": "#2196f3",
                "description": "体现逻辑、秩序与系统性"
            },
            {
                "label": "苏格拉底式 (Socratic)",
                "value": "socratic",
                "color": "#ff9800",
                "description": "象征启发性、智慧与思辨对话"
            }
    ]
    
    if personality_value:
        for option in personality_options:
            if option['value'] == personality_value:
                return option['label'], option['color']
    
    # 如果没有找到匹配项，返回原始值和默认颜色
    return personality_value, "#666666"

router = APIRouter(prefix="/ai-chat", tags=["ai-chat"])


# Dependency to get current user from JWT token
def get_current_user_from_token(token_data: TokenData = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    logger.info(f"Getting current user from token data: {token_data.email}")
    # Extract the email from token_data and get the user from DB
    from app.services.user import get_user_by_email
    user = get_user_by_email(db, email=token_data.email)
    if user is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# AI Chat Group Endpoints
@router.post("/groups/", response_model=AiChatGroupResponse)
def create_ai_chat_group_endpoint(
    group: AiChatGroupCreate,
    current_user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """创建新群聊"""
    # Automatically set the user_id from the authenticated user
    group_with_user = group.model_copy(update={"user_id": current_user.id})
    return create_ai_chat_group(db=db, group=group_with_user)


@router.get("/groups/{group_id}", response_model=AiChatGroupResponse)
def read_ai_chat_group(group_id: int, db: Session = Depends(get_db)):
    """根据ID获取群聊"""
    db_group = get_ai_chat_group(db=db, group_id=group_id)
    if db_group is None:
        raise HTTPException(status_code=404, detail="群聊不存在")
    return db_group


@router.put("/groups/{group_id}", response_model=AiChatGroupResponse)
def update_ai_chat_group_endpoint(
    group_id: int,
    group_update: AiChatGroupUpdate,
    current_user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """更新群聊信息"""
    # Verify that the user owns the group
    db_group = get_ai_chat_group(db=db, group_id=group_id)
    if db_group and db_group.user_id:
        if db_group.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限修改此群聊")

    db_group = update_ai_chat_group(db=db, group_id=group_id, group_update=group_update)
    if db_group is None:
        raise HTTPException(status_code=404, detail="群聊不存在")
    return db_group


@router.delete("/groups/{group_id}")
def delete_ai_chat_group_endpoint(
    group_id: int,
    current_user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """删除群聊"""
    # Verify that the user owns the group
    db_group = get_ai_chat_group(db=db, group_id=group_id)
    if db_group and db_group.user_id:
        if db_group.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限删除此群聊")

    db_group = delete_ai_chat_group(db=db, group_id=group_id)
    if db_group is None:
        raise HTTPException(status_code=404, detail="群聊不存在")
    return {"message": "群聊删除成功"}


@router.get("/groups/", response_model=PaginatedGroups)
def read_ai_chat_groups(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="每页显示的记录数"),
    status: Optional[str] = Query(None, description="群聊状态筛选"),
    user_id: Optional[int] = Query(None, description="创建人ID筛选"),
    current_user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """获取群聊列表（支持分页、状态筛选和用户筛选）"""
    # If user_id is not provided in query, use the authenticated user's ID
    if user_id is None:
        user_id = current_user.id

    groups, total = get_ai_chat_groups(db=db, skip=skip, limit=limit, status=status, user_id=user_id)

    # 计算总页数
    pages = (total + limit - 1) // limit

    return PaginatedGroups(
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        pages=pages,
        data=groups
    )


# AI Group Member Endpoints
@router.post("/members/", response_model=AiGroupMemberResponse)
def create_ai_group_member_endpoint(member: AiGroupMemberCreate, db: Session = Depends(get_db)):
    """添加群成员"""
    return create_ai_group_member(db=db, member=member)


@router.get("/members/{member_id}", response_model=AiGroupMemberResponse)
def read_ai_group_member(member_id: int, db: Session = Depends(get_db)):
    """根据ID获取群成员"""
    db_member = get_ai_group_member(db=db, member_id=member_id)
    if db_member is None:
        raise HTTPException(status_code=404, detail="群成员不存在")
    return db_member


@router.put("/members/{member_id}", response_model=AiGroupMemberResponse)
def update_ai_group_member_endpoint(
    member_id: int, member_update: AiGroupMemberUpdate, db: Session = Depends(get_db)
):
    """更新群成员信息"""
    db_member = update_ai_group_member(db=db, member_id=member_id, member_update=member_update)
    if db_member is None:
        raise HTTPException(status_code=404, detail="群成员不存在")
    return db_member


@router.delete("/members/{member_id}")
def delete_ai_group_member_endpoint(member_id: int, db: Session = Depends(get_db)):
    """删除群成员"""
    db_member = delete_ai_group_member(db=db, member_id=member_id)
    if db_member is None:
        raise HTTPException(status_code=404, detail="群成员不存在")
    return {"message": "群成员删除成功"}


@router.get("/groups/{group_id}/members", response_model=PaginatedMembers)
def read_ai_group_members(
    group_id: int,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="每页显示的记录数"),
    member_type: Optional[int] = Query(None, description="成员类型筛选：0为人，1为AI"),
    db: Session = Depends(get_db)
):
    """获取群成员列表（支持分页和成员类型筛选）"""
    members, total = get_ai_group_members(db=db, group_id=group_id, skip=skip, limit=limit, member_type=member_type)

    # 计算总页数
    pages = (total + limit - 1) // limit

    return PaginatedMembers(
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        pages=pages,
        data=members
    )


# AI Message Endpoints
@router.post("/messages/", response_model=AiMessageResponse)
def create_ai_message_endpoint(
    message: AiMessageCreate,
    current_user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """创建新消息"""
    from app.models.ai_chat import AiGroupMember
    from app.services.user import get_user_by_email
    
    # 获取当前用户
    user = get_user_by_email(db, current_user.email)
    
    # 根据group_id和user_id从ai_group_members表中获取member_type=0的记录
    group_member = db.query(AiGroupMember)\
        .filter(AiGroupMember.group_id == message.group_id)\
        .filter(AiGroupMember.user_id == user.id)\
        .filter(AiGroupMember.member_type == 0)\
        .first()
    
    if not group_member:
        raise HTTPException(
            status_code=404,
            detail="Group member not found for the user in this group"
        )
    
    # 更新message的member_id为找到的group_member的id
    message_data = message.model_dump()
    message_data['member_id'] = group_member.id
    
    # 创建消息
    from app.schemas.ai_chat import AiMessageCreate
    updated_message = AiMessageCreate(**message_data)
    return create_ai_message(db=db, message=updated_message)


@router.get("/messages/{message_id}", response_model=AiMessageResponse)
def read_ai_message(message_id: int, db: Session = Depends(get_db)):
    """根据ID获取消息"""
    db_message = get_ai_message(db=db, message_id=message_id)
    if db_message is None:
        raise HTTPException(status_code=404, detail="消息不存在")
    return db_message


@router.put("/messages/{message_id}", response_model=AiMessageResponse)
def update_ai_message_endpoint(
    message_id: int, message_update: AiMessageUpdate, db: Session = Depends(get_db)
):
    """更新消息信息"""
    db_message = update_ai_message(db=db, message_id=message_id, message_update=message_update)
    if db_message is None:
        raise HTTPException(status_code=404, detail="消息不存在")
    return db_message


@router.delete("/messages/{message_id}")
def delete_ai_message_endpoint(message_id: int, db: Session = Depends(get_db)):
    """删除消息"""
    db_message = delete_ai_message(db=db, message_id=message_id)
    if db_message is None:
        raise HTTPException(status_code=404, detail="消息不存在")
    return {"message": "消息删除成功"}


@router.get("/groups/{group_id}/messages", response_model=PaginatedMessages)
def read_ai_messages(
    group_id: int,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="每页显示的记录数"),
    db: Session = Depends(get_db)
):
    """获取群聊消息列表（支持分页）"""
    messages, total = get_ai_messages(db=db, group_id=group_id, skip=skip, limit=limit)

    # 计算总页数
    pages = (total + limit - 1) // limit

    return PaginatedMessages(
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        pages=pages,
        data=messages
    )


@router.get("/groups/{group_id}/message-list")
def get_message_list(
    group_id: int,
    db: Session = Depends(get_db)
):
    """根据群组ID获取消息列表，按指定格式返回"""
    from app.models.ai_chat import AiMessage, AiGroupMember
    
    # 查询消息及关联的成员信息
    messages = db.query(AiMessage, AiGroupMember)\
        .join(AiGroupMember, AiMessage.member_id == AiGroupMember.id)\
        .filter(AiMessage.group_id == group_id)\
        .order_by(AiMessage.created_at.asc())\
        .all()
    
    result = []
    for msg, member in messages:
        # 确定消息类型
        msg_type = 'ai' if member and member.member_type == 1 else 'user'
        
        # 设置消息发送者姓名
        name = ""
        if member:
            if member.member_type == 1:  # AI
                name = member.ai_nickname
            elif member.user_id:  # Human user
                from app.services.user import get_user_by_id
                user = get_user_by_id(db, member.user_id)
                if user:
                    name = user.username or user.email
                else:
                    name = "Unknown User"
            else:
                name = "Unknown Member"
        else:
            name = "System"
        
        # 为每个用户/ai分配固定的颜色
        colors = ['#ff9800', '#2196f3', '#9c27b0', '#4caf50', '#f44336', '#e91e63', '#673ab7', '#3f51b5', '#00bcd4', '#009688']
        
        # 根据personality的值获取对应的中文标签和颜色
        personality_value = getattr(member, 'personality', '') if member else ''
        tag_label, tag_type_color = get_personality_info(personality_value)
        
        # 构建消息对象
        message_obj = {
            "id": msg.id,
            "type": msg_type,
            "content": msg.content,
            "avatar": name[0].upper() if name else None,  # 取名字的首字母
            "name": name,
            "tag": tag_label,  # 对应personality字段的中文标签
            "tagType": tag_type_color,  # 对应personality的颜色
            "likes": 0,  # 默认值，如果有点赞功能可以查询
            "avatarColor": tag_type_color  # 使用基于名称的固定颜色
        }
        
        result.append(message_obj)
    
    return result


# AI Model Endpoints
@router.post("/models/", response_model=AiModelResponse)
def create_ai_model_endpoint(model: AiModelCreate, db: Session = Depends(get_db)):
    """创建新AI模型"""
    return create_ai_model(db=db, model=model)


@router.get("/models/{model_id}", response_model=AiModelResponse)
def read_ai_model(model_id: int, db: Session = Depends(get_db)):
    """根据ID获取AI模型"""
    db_model = get_ai_model(db=db, model_id=model_id)
    if db_model is None:
        raise HTTPException(status_code=404, detail="AI模型不存在")
    return db_model


@router.put("/models/{model_id}", response_model=AiModelResponse)
def update_ai_model_endpoint(
    model_id: int, model_update: AiModelUpdate, db: Session = Depends(get_db)
):
    """更新AI模型信息"""
    db_model = update_ai_model(db=db, model_id=model_id, model_update=model_update)
    if db_model is None:
        raise HTTPException(status_code=404, detail="AI模型不存在")
    return db_model


@router.delete("/models/{model_id}")
def delete_ai_model_endpoint(model_id: int, db: Session = Depends(get_db)):
    """删除AI模型"""
    db_model = delete_ai_model(db=db, model_id=model_id)
    if db_model is None:
        raise HTTPException(status_code=404, detail="AI模型不存在")
    return {"message": "AI模型删除成功"}


@router.get("/models/", response_model=PaginatedModels)
def read_ai_models(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="每页显示的记录数"),
    is_active: Optional[bool] = Query(None, description="AI模型激活状态筛选"),
    db: Session = Depends(get_db)
):
    """获取AI模型列表（支持分页和激活状态筛选）"""
    models, total = get_ai_models(db=db, skip=skip, limit=limit, is_active=is_active)

    # 计算总页数
    pages = (total + limit - 1) // limit

    return PaginatedModels(
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        pages=pages,
        data=models
    )