"""
AI群聊主服务
整合所有组件，提供完整的AI群聊功能
"""

from __future__ import annotations
import asyncio
from typing import Optional
from sqlalchemy.orm import Session
from app.models.ai_chat import AiGroupMember, AiMessage, AiModel, AiChatGroup
from app.services.ai_model_service import AiModelService
from app.services.ai_character_service import AiCharacterService, CharacterDriftPrevention, ConsistencyReinforcement
from app.services.ai_context_manager import SelectiveContextProvider, ConversationContextManager, build_context_aware_prompt
from app.services.ai_relevance_detector import SmartTriggerDetector


class AiGroupChatService:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.ai_model_service = AiModelService(db_session)
        self.character_service = AiCharacterService(db_session)
        self.context_provider = SelectiveContextProvider(db_session)
        self.conversation_manager = ConversationContextManager(db_session)
        self.drift_prevention = CharacterDriftPrevention(db_session)
        self.trigger_detector = SmartTriggerDetector(db_session)

    async def generate_response(
        self,
        member_id: int,
        group_id: int,
        trigger_message: Optional[str] = None
    ) -> str:
        """生成AI响应"""
        
        # 1. 验证AI成员存在
        ai_member = self.db.query(AiGroupMember).filter(
            AiGroupMember.id == member_id
        ).first()
        
        if not ai_member:
            raise ValueError(f"AI成员不存在: {member_id}")

        # 2. 验证AI模型存在且激活
        if ai_member.ai_model is None or not ai_member.ai_model.strip():
            raise ValueError(f"AI成员缺少模型配置: {member_id}")

        ai_model = self.db.query(AiModel).filter(
            AiModel.model_name == ai_member.ai_model
        ).first()

        if not ai_model or (hasattr(ai_model, 'is_active') and ai_model.is_active is False):
            raise ValueError(f"AI模型不可用: {ai_member.ai_model}")

        # 3. 获取完整的对话上下文
        conversation_context = self.conversation_manager.build_conversation_context(group_id)

        # 4. 构建角色提示
        character_prompt = self.character_service.get_character_prompt(member_id)

        # 5. 构建上下文感知的完整提示
        full_prompt = build_context_aware_prompt(
            character_prompt=character_prompt,
            conversation_context=conversation_context,
            target_member_nickname=ai_member.ai_nickname if ai_member.ai_nickname is not None else "",
            target_member_personality=ai_member.personality if ai_member.personality is not None else "",
            target_member_stance=ai_member.initial_stance if ai_member.initial_stance is not None else ""
        )

        # 如果有触发消息，将其添加到提示中
        if trigger_message is not None and trigger_message.strip():
            full_prompt += f"\n\n有人特别提到你并询问：{trigger_message}\n请回应这个问题。"

        # 6. 调用AI模型生成响应
        try:
            response = await self.ai_model_service.generate(
                model_name=ai_member.ai_model,
                prompt=full_prompt,
                max_tokens=500,
                temperature=0.7
            )
        except Exception as e:
            raise RuntimeError(f"AI模型调用失败: {str(e)}")

        # 7. 检查角色漂移
        if self.drift_prevention.detect_drift(member_id, response):
            # 如果检测到漂移，尝试修正
            response = await self._correct_response_if_drifting(
                member_id, response, full_prompt
            )

        return response

    async def _correct_response_if_drifting(
        self,
        member_id: int,
        original_response: str,
        original_prompt: str
    ) -> str:
        """如果检测到角色漂移，修正响应"""
        
        # 获取AI的强化提示
        reinforcement_prompt = ConsistencyReinforcement(self.db).reinforce_character(
            member_id, []
        )

        # 重新生成响应，加强角色特征
        ai_member = self.db.query(AiGroupMember).filter(
            AiGroupMember.id == member_id
        ).first()

        correction_prompt = f"""
{reinforcement_prompt}

原始请求：
{original_prompt}

原始响应：
{original_response}

请重新生成响应，确保完全符合你的角色特征和立场。
"""

        try:
            corrected_response = await self.ai_model_service.generate(
                model_name=ai_member.ai_model,
                prompt=correction_prompt,
                max_tokens=500,
                temperature=0.6  # 稍微降低随机性以提高一致性
            )
        except Exception as e:
            # 如果修正失败，返回原始响应并记录警告
            print(f"警告：AI响应修正失败: {str(e)}")
            return original_response

        return corrected_response

    def validate_ai_member(self, member_id: int, group_id: int) -> bool:
        """验证AI成员的有效性"""
        ai_member = self.db.query(AiGroupMember).filter(
            AiGroupMember.id == member_id,
            AiGroupMember.group_id == group_id
        ).first()
        
        return ai_member is not None

    def validate_group_exists(self, group_id: int) -> bool:
        """验证群组是否存在"""
        group = self.db.query(AiChatGroup).filter(
            AiChatGroup.id == group_id
        ).first()
        
        return group is not None