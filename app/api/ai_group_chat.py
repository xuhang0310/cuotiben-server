"""
AI群聊功能API端点
实现多AI角色差异化群聊的核心功能
此API专注于AI特有的功能，如AI响应触发和AI角色差异化
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
from app.database.session import get_db
from app.models.ai_chat import AiGroupMember, AiMessage, AiChatGroup, AiModel
from app.services.ai_group_chat_service import AiGroupChatService
from app.services.ai_relevance_detector import MessageRelevanceDetector, SmartTriggerDetector
from app.services.ai_context_manager import ConversationContextManager, SelectiveContextProvider
from app.services.ai_character_service import AiCharacterService, CharacterDriftPrevention, RoleConsistencyMiddleware
from app.services.mention_parser import MentionParser

router = APIRouter(prefix="/ai-group-chat", tags=["AI Group Chat"])

# 请求模型
class TriggerAIResponseRequest(BaseModel):
    group_id: int
    member_id: int
    trigger_message: Optional[str] = None
    force_trigger: bool = False
    
    @validator('trigger_message')
    def validate_trigger_message(cls, v):
        if v and len(v) > 1000:
            raise ValueError('触发消息不能超过1000个字符')
        return v

# 响应模型
class ApiResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class AIResponseResponse(BaseModel):
    message_id: int
    content: str
    created_at: datetime

# API端点
import logging

logger = logging.getLogger(__name__)

@router.post("/ai/respond", response_model=ApiResponse)
async def trigger_ai_response(
    request: TriggerAIResponseRequest,
    db: Session = Depends(get_db)
):
    """
    触发AI成员响应
    这是AI群聊的核心功能，根据AI的人格和立场生成差异化响应
    """
    try:
        logger.info(f"Trigger AI Response called with request: {request.dict()}")
        
        # 获取AI成员信息
        logger.info(f"Querying AI member with ID: {request.member_id}")
        ai_member = db.query(AiGroupMember).filter(
            AiGroupMember.id == request.member_id
        ).first()

        if not ai_member:
            logger.error(f"AI member with ID {request.member_id} not found")
            raise HTTPException(status_code=404, detail="AI成员不存在")

        logger.info(f"Found AI member: {ai_member.id}, checking group membership")
        
        # 验证群组和成员的匹配
        if ai_member.group_id != request.group_id:
            logger.error(f"AI member {request.member_id} does not belong to group {request.group_id}")
            raise HTTPException(status_code=400, detail="AI成员不属于指定群组")

        logger.info("Validating AI member fields...")
        
        # 验证AI成员的必要字段是否存在 - 使用 is None instead of not for SQLAlchemy compatibility
        logger.info("Checking for None values in required fields...")
        if ai_member.ai_model is None:
            logger.error(f"AI member {request.member_id} model configuration is None")
            raise HTTPException(status_code=400, detail="AI成员模型配置为None")
        if ai_member.ai_nickname is None:
            logger.error(f"AI member {request.member_id} nickname is None")
            raise HTTPException(status_code=400, detail="AI成员昵称为None")
        if ai_member.personality is None:
            logger.error(f"AI member {request.member_id} personality is None")
            raise HTTPException(status_code=400, detail="AI成员人格特征为None")
        if ai_member.initial_stance is None:
            logger.error(f"AI member {request.member_id} initial stance is None")
            raise HTTPException(status_code=400, detail="AI成员初始立场为None")

        logger.info("Checking if AI should be triggered...")
        
        # 检查是否应该触发AI（除非强制触发或提供了触发消息）
        # 如果提供了触发消息，视为用户明确要求AI回应，应跳过相关性检测
        should_skip_relevance_check = request.force_trigger or (request.trigger_message is not None and request.trigger_message.strip() != "")
        if not should_skip_relevance_check:
            logger.info("Not forcing trigger and no trigger message, using SmartTriggerDetector")
            trigger_detector = SmartTriggerDetector(db)
            should_trigger_result = trigger_detector.should_trigger_ai(
                request.group_id,
                request.member_id,
                request.trigger_message
            )
            logger.info(f"SmartTriggerDetector result: {should_trigger_result}")

            if not should_trigger_result:
                trigger_reasons = trigger_detector.get_trigger_reasons(
                    request.group_id,
                    request.member_id
                )
                logger.info(f"Trigger reasons: {trigger_reasons}")
                return ApiResponse(
                    success=False,
                    message="AI认为当前不需要回应",
                    data={"reasons": trigger_reasons}
                )

        # 创建AI群聊服务实例
        logger.info("Creating AiGroupChatService instance")
        ai_service = AiGroupChatService(db)

        # 验证AI成员是否有效
        logger.info("Validating AI member with service")
        is_valid = ai_service.validate_ai_member(request.member_id, request.group_id)
        logger.info(f"AI member validation result: {is_valid}")
        
        if not is_valid:
            logger.error(f"AI member {request.member_id} validation failed")
            raise HTTPException(status_code=404, detail="AI成员不存在或不属于该群组")

        # 生成AI响应
        logger.info("Generating AI response...")
        response = await ai_service.generate_response(
            member_id=request.member_id,
            group_id=request.group_id,
            trigger_message=request.trigger_message
        )
        logger.info(f"Generated response: {response[:100]}...")  # Log first 100 chars

        # 保存响应到数据库
        logger.info("Saving response to database...")
        new_message = AiMessage(
            group_id=request.group_id,
            member_id=request.member_id,
            content=response,
            message_type='text'
        )
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        logger.info(f"Saved message with ID: {new_message.id}")

        return ApiResponse(
            success=True,
            message="AI响应生成成功",
            data={
                "message_id": new_message.id,
                "content": response,
                "created_at": new_message.created_at
            }
        )
    except HTTPException:
        logger.error("HTTPException caught", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in trigger_ai_response: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"AI响应生成失败: {str(e)}")


@router.get("/group/{group_id}", response_model=ApiResponse)
async def get_group_detail(
    group_id: int,
    db: Session = Depends(get_db)
):
    """
    获取群组详情
    包括成员信息（特别是AI成员的人格和立场）和消息
    """
    try:
        group = db.query(AiChatGroup).filter(AiChatGroup.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="群组不存在")
        
        # 获取群组成员
        members = db.query(AiGroupMember).filter(
            AiGroupMember.group_id == group_id
        ).all()
        
        member_list = []
        for member in members:
            member_data = {
                "id": member.id,
                "nickname": member.ai_nickname,
                "member_type": member.member_type,
                "personality": member.personality,
                "initial_stance": member.initial_stance
            }
            member_list.append(member_data)
        
        # 获取群组消息
        messages = db.query(AiMessage).filter(
            AiMessage.group_id == group_id
        ).order_by(AiMessage.created_at.desc()).limit(50).all()  # 获取最近50条消息
        
        message_list = []
        for msg in reversed(messages):  # 按时间顺序排列
            sender = db.query(AiGroupMember).filter(
                AiGroupMember.id == msg.member_id
            ).first()
            
            message_data = {
                "id": msg.id,
                "sender_nickname": sender.ai_nickname if sender else "Unknown",
                "content": msg.content,
                "message_type": msg.message_type,
                "created_at": msg.created_at
            }
            message_list.append(message_data)
        
        return ApiResponse(
            success=True,
            data={
                "id": group.id,
                "name": group.name,
                "created_at": group.created_at,
                "members": member_list,
                "messages": message_list
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取群组详情失败: {str(e)}")


@router.get("/messages/{group_id}", response_model=ApiResponse)
async def get_group_messages(
    group_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """获取群组消息"""
    try:
        # 验证群组是否存在
        group = db.query(AiChatGroup).filter(AiChatGroup.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="群组不存在")
        
        messages = db.query(AiMessage).filter(
            AiMessage.group_id == group_id
        ).order_by(AiMessage.created_at.desc()).offset(skip).limit(limit).all()
        
        result_messages = []
        for msg in reversed(messages):  # 按时间顺序排列
            sender = db.query(AiGroupMember).filter(
                AiGroupMember.id == msg.member_id
            ).first()
            
            message_data = {
                "id": msg.id,
                "member_id": msg.member_id,
                "sender_nickname": sender.ai_nickname if sender else "Unknown",
                "content": msg.content,
                "message_type": msg.message_type,
                "created_at": msg.created_at
            }
            result_messages.append(message_data)
        
        return ApiResponse(
            success=True,
            data={
                "messages": result_messages,
                "pagination": {
                    "skip": skip,
                    "limit": limit,
                    "total": len(result_messages)
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取消息失败: {str(e)}")


@router.get("/ai-member/{member_id}/characteristics", response_model=ApiResponse)
async def get_ai_characteristics(
    member_id: int,
    db: Session = Depends(get_db)
):
    """
    获取AI成员的特征信息
    用于前端显示AI的人格和立场信息
    """
    try:
        ai_member = db.query(AiGroupMember).filter(
            AiGroupMember.id == member_id
        ).first()
        
        if not ai_member:
            raise HTTPException(status_code=404, detail="AI成员不存在")
        
        return ApiResponse(
            success=True,
            data={
                "id": ai_member.id,
                "nickname": ai_member.ai_nickname,
                "personality": ai_member.personality,
                "initial_stance": ai_member.initial_stance,
                "ai_model": ai_member.ai_model
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取AI特征失败: {str(e)}")


# ==================== @提及功能API ====================

class SendMessageRequest(BaseModel):
    """发送消息请求"""
    content: str
    sender_member_id: int

    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('消息内容不能为空')
        if len(v) > 2000:
            raise ValueError('消息内容不能超过2000个字符')
        return v.strip()


class AIResponseItem(BaseModel):
    """单个AI响应项"""
    member_id: int
    nickname: str
    content: str
    message_id: int
    created_at: datetime


class SendMessageResponse(BaseModel):
    """发送消息响应"""
    user_message_id: int
    mentioned_ai_count: int
    ai_responses: List[AIResponseItem]


@router.post("/group/{group_id}/send", response_model=ApiResponse)
async def send_message(
    group_id: int,
    request: SendMessageRequest,
    db: Session = Depends(get_db)
):
    """
    发送消息并触发@提及的AI响应

    - 如果消息包含@昵称，只触发被@的AI（按@的顺序）
    - 如果没有@，不触发任何AI（后续可扩展为智能触发）
    """
    try:
        logger.info(f"Send message to group {group_id}: {request.content}")

        # 1. 验证群组存在
        group = db.query(AiChatGroup).filter(AiChatGroup.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="群组不存在")

        # 2. 验证发送者存在且属于该群组
        sender = db.query(AiGroupMember).filter(
            AiGroupMember.id == request.sender_member_id,
            AiGroupMember.group_id == group_id
        ).first()

        if not sender:
            raise HTTPException(status_code=404, detail="发送者不存在或不属于该群组")

        # 3. 保存用户消息
        user_message = AiMessage(
            group_id=group_id,
            member_id=request.sender_member_id,
            content=request.content,
            message_type='text'
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        logger.info(f"User message saved: {user_message.id}")

        # 4. 解析@提及
        mention_parser = MentionParser(db)
        mentioned_members = mention_parser.parse_mentions_in_group(
            content=request.content,
            group_id=group_id
        )

        if not mentioned_members:
            logger.info("No mentions found, returning user message only")
            return ApiResponse(
                success=True,
                message="消息已发送，未触发AI（无@提及）",
                data={
                    "user_message_id": user_message.id,
                    "mentioned_ai_count": 0,
                    "ai_responses": []
                }
            )

        logger.info(f"Found {len(mentioned_members)} mentioned AI members: "
                   f"{[m.ai_nickname for m in mentioned_members]}")

        # 5. 按顺序依次触发被@的AI
        ai_service = AiGroupChatService(db)
        ai_responses = []

        for member in mentioned_members:
            try:
                logger.info(f"Generating response for AI member: {member.ai_nickname} (ID: {member.id})")

                # 验证AI成员配置完整
                if not member.ai_model or not member.personality:
                    logger.warning(f"AI member {member.id} missing configuration, skipping")
                    continue

                # 生成AI响应（将用户消息作为触发消息）
                response_content = await ai_service.generate_response(
                    member_id=member.id,
                    group_id=group_id,
                    trigger_message=request.content
                )

                # 保存AI响应
                ai_message = AiMessage(
                    group_id=group_id,
                    member_id=member.id,
                    content=response_content,
                    message_type='text'
                )
                db.add(ai_message)
                db.commit()
                db.refresh(ai_message)

                ai_responses.append(AIResponseItem(
                    member_id=member.id,
                    nickname=member.ai_nickname or "Unknown",
                    content=response_content,
                    message_id=ai_message.id,
                    created_at=ai_message.created_at
                ))

                logger.info(f"AI {member.ai_nickname} response saved: {ai_message.id}")

            except Exception as e:
                logger.error(f"Failed to generate response for AI {member.id}: {str(e)}")
                # 继续处理下一个AI，不中断流程
                continue

        return ApiResponse(
            success=True,
            message=f"消息已发送，触发了{len(ai_responses)}个AI响应",
            data={
                "user_message_id": user_message.id,
                "mentioned_ai_count": len(mentioned_members),
                "ai_responses": [response.dict() for response in ai_responses]
            }
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in send_message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")


@router.post("/group/{group_id}/send-without-ai", response_model=ApiResponse)
async def send_message_without_ai(
    group_id: int,
    request: SendMessageRequest,
    db: Session = Depends(get_db)
):
    """
    仅发送消息，不触发任何AI响应
    用于前端发送消息后手动控制AI触发
    """
    try:
        # 验证群组存在
        group = db.query(AiChatGroup).filter(AiChatGroup.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="群组不存在")

        # 验证发送者存在
        sender = db.query(AiGroupMember).filter(
            AiGroupMember.id == request.sender_member_id,
            AiGroupMember.group_id == group_id
        ).first()

        if not sender:
            raise HTTPException(status_code=404, detail="发送者不存在或不属于该群组")

        # 保存消息
        user_message = AiMessage(
            group_id=group_id,
            member_id=request.sender_member_id,
            content=request.content,
            message_type='text'
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)

        return ApiResponse(
            success=True,
            message="消息已发送",
            data={
                "message_id": user_message.id,
                "content": user_message.content,
                "created_at": user_message.created_at
            }
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in send_message_without_ai: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")