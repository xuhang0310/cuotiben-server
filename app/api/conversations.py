from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database.session import get_db
from app.schemas.conversation import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    ConversationMemberCreate, ConversationMemberUpdate, ConversationMemberResponse,
    ChatMessageCreate, ChatMessageUpdate, ChatMessageResponse,
    PaginatedConversations, PaginatedMembers, PaginatedMessages, ConversationMemberWithUserInfo
)
from app.services.conversation import (
    get_conversation, get_conversations, create_conversation, update_conversation, delete_conversation,
    get_conversation_member, get_conversation_members, add_conversation_member, 
    update_conversation_member, remove_conversation_member, get_user_conversations,
    get_chat_messages, create_chat_message, update_chat_message, delete_chat_message,
    get_user_messages, remove_user_from_conversation
)

router = APIRouter(prefix="", tags=["conversations"])


# 会话相关API
@router.post("/", response_model=ConversationResponse)
def create_conversation_endpoint(conversation: ConversationCreate, db: Session = Depends(get_db)):
    """创建新会话"""
    return create_conversation(db=db, conversation=conversation)


@router.get("/{conversation_id}", response_model=ConversationResponse)
def read_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """根据ID获取会话"""
    db_conversation = get_conversation(db=db, conversation_id=conversation_id)
    if db_conversation is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return db_conversation


@router.put("/{conversation_id}", response_model=ConversationResponse)
def update_conversation_endpoint(
    conversation_id: str, conversation_update: ConversationUpdate, db: Session = Depends(get_db)
):
    """更新会话信息"""
    db_conversation = update_conversation(db=db, conversation_id=conversation_id, conversation_update=conversation_update)
    if db_conversation is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return db_conversation


@router.delete("/{conversation_id}")
def delete_conversation_endpoint(conversation_id: str, db: Session = Depends(get_db)):
    """删除会话"""
    db_conversation = delete_conversation(db=db, conversation_id=conversation_id)
    if db_conversation is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"message": "会话删除成功"}


@router.get("/", response_model=PaginatedConversations)
def read_conversations(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="每页显示的记录数"),
    conversation_type: Optional[str] = Query(None, description="会话类型筛选"),
    db: Session = Depends(get_db)
):
    """获取会话列表（支持分页和类型筛选）"""
    conversations, total = get_conversations(db=db, skip=skip, limit=limit, conversation_type=conversation_type)
    
    # 计算总页数
    pages = (total + limit - 1) // limit
    
    return PaginatedConversations(
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        pages=pages,
        data=conversations
    )


# 会话成员相关API
@router.post("/members/", response_model=ConversationMemberResponse)
def add_member_to_conversation(member: ConversationMemberCreate, db: Session = Depends(get_db)):
    """添加会话成员"""
    return add_conversation_member(db=db, member=member)


@router.get("/members/{member_id}", response_model=ConversationMemberResponse)
def read_conversation_member(member_id: int, db: Session = Depends(get_db)):
    """根据ID获取会话成员"""
    db_member = get_conversation_member(db=db, member_id=member_id)
    if db_member is None:
        raise HTTPException(status_code=404, detail="会话成员不存在")
    return db_member


@router.put("/members/{member_id}", response_model=ConversationMemberResponse)
def update_conversation_member_endpoint(
    member_id: int, member_update: ConversationMemberUpdate, db: Session = Depends(get_db)
):
    """更新会话成员信息"""
    db_member = update_conversation_member(db=db, member_id=member_id, member_update=member_update)
    if db_member is None:
        raise HTTPException(status_code=404, detail="会话成员不存在")
    return db_member


@router.delete("/members/{member_id}")
def remove_conversation_member_endpoint(member_id: int, db: Session = Depends(get_db)):
    """移除会话成员"""
    db_member = remove_conversation_member(db=db, member_id=member_id)
    if db_member is None:
        raise HTTPException(status_code=404, detail="会话成员不存在")
    return {"message": "会话成员移除成功"}


@router.get("/{conversation_id}/members", response_model=PaginatedMembers)
def read_conversation_members(
    conversation_id: str,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="每页显示的记录数"),
    db: Session = Depends(get_db)
):
    """获取会话成员列表（支持分页）"""
    from app.models.conversation import ConversationMember
    from app.models.historical_figure import HistoricalFigure
    from app.schemas.conversation import ConversationMemberWithUserInfo

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
    members = []
    for member, member_name, avatar in results:
        member_response = ConversationMemberWithUserInfo(
            conversation_id=member.conversation_id,
            user_id=member.user_id,
            user_role=member.user_role,
            id=member.id,
            joined_at=member.joined_at,
            member_name=member_name,
            avatar=avatar
        )
        members.append(member_response)

    # 计算总页数
    pages = (total + limit - 1) // limit

    return PaginatedMembers(
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        pages=pages,
        data=members
    )


@router.get("/user/{user_id}/conversations", response_model=PaginatedConversations)
def read_user_conversations(
    user_id: int,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="每页显示的记录数"),
    db: Session = Depends(get_db)
):
    """获取用户参与的所有会话"""
    conversations, total = get_user_conversations(db=db, user_id=user_id, skip=skip, limit=limit)
    
    # 计算总页数
    pages = (total + limit - 1) // limit
    
    return PaginatedConversations(
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        pages=pages,
        data=conversations
    )


@router.delete("/{conversation_id}/members/user/{user_id}")
def remove_user_from_conversation_endpoint(conversation_id: str, user_id: int, db: Session = Depends(get_db)):
    """将用户从会话中移除"""
    db_member = remove_user_from_conversation(db=db, conversation_id=conversation_id, user_id=user_id)
    if db_member is None:
        raise HTTPException(status_code=404, detail="用户不在该会话中")
    return {"message": "用户已从会话中移除"}


# 消息相关API
@router.post("/messages/", response_model=ChatMessageResponse)
def create_message(message: ChatMessageCreate, db: Session = Depends(get_db)):
    """创建新消息"""
    return create_chat_message(db=db, message=message)


@router.get("/messages/{message_id}", response_model=ChatMessageResponse)
def read_message(message_id: int, db: Session = Depends(get_db)):
    """根据ID获取消息"""
    db_message = get_chat_message(db=db, message_id=message_id)
    if db_message is None or db_message.is_deleted == 1:
        raise HTTPException(status_code=404, detail="消息不存在")
    return db_message


@router.put("/messages/{message_id}", response_model=ChatMessageResponse)
def update_message_endpoint(
    message_id: int, message_update: ChatMessageUpdate, db: Session = Depends(get_db)
):
    """更新消息信息"""
    db_message = update_chat_message(db=db, message_id=message_id, message_update=message_update)
    if db_message is None:
        raise HTTPException(status_code=404, detail="消息不存在")
    return db_message


@router.delete("/messages/{message_id}")
def delete_message_endpoint(message_id: int, db: Session = Depends(get_db)):
    """删除消息（软删除）"""
    db_message = delete_chat_message(db=db, message_id=message_id)
    if db_message is None:
        raise HTTPException(status_code=404, detail="消息不存在")
    return {"message": "消息已删除"}


@router.get("/{conversation_id}/messages", response_model=PaginatedMessages)
def read_messages(
    conversation_id: str,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="每页显示的记录数"),
    db: Session = Depends(get_db)
):
    """获取会话中的消息列表（支持分页）"""
    messages, total = get_chat_messages(db=db, conversation_id=conversation_id, skip=skip, limit=limit)

    # 处理头像URL - 如果不是以http开头，则拼接域名
    processed_messages = []
    for message in messages:
        message_dict = message.__dict__.copy()  # 创建副本以避免修改原始对象
        if hasattr(message, 'avatar') and message.avatar:
            avatar = message.avatar
            # 如果头像URL不是以http开头，则拼接域名
            if not avatar.lower().startswith(('http://', 'https://')):
                message_dict['avatar'] = f"http://180.76.183.241/{avatar.lstrip('/')}"
        processed_messages.append(ChatMessageResponse(**message_dict))

    # 计算总页数
    pages = (total + limit - 1) // limit

    return PaginatedMessages(
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        pages=pages,
        data=processed_messages
    )


@router.get("/user/{user_id}/messages", response_model=PaginatedMessages)
def read_user_messages(
    user_id: int,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="每页显示的记录数"),
    db: Session = Depends(get_db)
):
    """获取用户发送的所有消息"""
    messages, total = get_user_messages(db=db, user_id=user_id, skip=skip, limit=limit)
    
    # 计算总页数
    pages = (total + limit - 1) // limit
    
    return PaginatedMessages(
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        pages=pages,
        data=messages
    )