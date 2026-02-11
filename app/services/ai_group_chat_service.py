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
from app.services.ai_context_manager import (
    SelectiveContextProvider,
    ConversationContextManager,
    build_context_aware_prompt,
    build_segmented_context_for_ai,
    build_enhanced_context,
    build_timeline_context,
    create_role_aware_prompt
)
from app.services.ai_relevance_detector import SmartTriggerDetector
from app.services.input_sanitizer_service import InputSanitizerService, SanitizationLevel
from app.services.secure_prompt_template_service import SecurePromptTemplateService
from app.services.context_isolation_service import ContextIsolationService
from app.services.security_check_service import SecurityCheckService
from app.services.output_validation_service import OutputValidationService


class AiGroupChatService:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.ai_model_service = AiModelService(db_session)
        self.character_service = AiCharacterService(db_session)
        self.context_provider = SelectiveContextProvider(db_session)
        self.conversation_manager = ConversationContextManager(db_session)
        self.drift_prevention = CharacterDriftPrevention(db_session)
        self.trigger_detector = SmartTriggerDetector(db_session)
        
        # 新增安全服务
        self.input_sanitizer = InputSanitizerService()
        self.prompt_template_service = SecurePromptTemplateService()
        self.context_isolation_service = ContextIsolationService(db_session)
        self.security_check_service = SecurityCheckService(db_session)
        self.output_validation_service = OutputValidationService(db_session)

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

        # 验证AI模型的必要字段是否存在
        if not ai_model.endpoint or not ai_model.endpoint.strip():
            raise ValueError(f"AI模型端点配置缺失: {ai_member.ai_model}")
        if not ai_model.api_key or not ai_model.api_key.strip():
            raise ValueError(f"AI模型API密钥配置缺失: {ai_member.ai_model}")

        # 3. 构建隔离的上下文（安全增强版）
        isolated_context = self.context_isolation_service.build_isolated_context(
            target_member_id=member_id,
            group_id=group_id,
            message_limit=20,
            include_trigger_message=trigger_message
        )

        # 4. 验证上下文完整性
        context_integrity = self.context_isolation_service.validate_context_integrity(isolated_context)
        if not context_integrity["overall_safe"]:
            raise ValueError(f"上下文完整性检查失败: {context_integrity}")

        # 5. 使用安全提示词模板构建提示词
        secure_messages = self.prompt_template_service.build_secure_messages(
            ai_member=ai_member,
            context=isolated_context["conversation_history"],
            user_message=isolated_context.get("trigger_message"),
            message_type="mention_triggered",
            sanitizer=self.input_sanitizer
        )

        # 6. 构建最终提示词（使用消息格式）
        full_prompt = ""
        for msg in secure_messages:
            full_prompt += f"{msg['role'].upper()}: {msg['content']}\n\n"

        # 7. 应用安全层检查
        try:
            secure_prompt = self.security_check_service.apply_security_layer(
                ai_member=ai_member,
                prompt=full_prompt
            )
        except ValueError as e:
            raise ValueError(f"安全检查失败: {str(e)}")

        # 8. 调用AI模型生成响应
        try:
            response = await self.ai_model_service.generate(
                model_name=ai_member.ai_model,
                prompt=secure_prompt,
                max_tokens=300,  # 控制回复长度
                temperature=0.8  # 增加一些随机性使回复更自然
            )
        except Exception as e:
            raise RuntimeError(f"AI模型调用失败: {str(e)}")

        # 9. 验证AI响应的安全性
        validation_result = self.output_validation_service.validate_and_correct_response(
            ai_member=ai_member,
            response=response,
            original_prompt=secure_prompt,
            auto_correct=True
        )

        if not validation_result["validation_result"]["is_valid"]:
            # 如果验证失败，可以选择抛出异常或返回默认响应
            raise ValueError(f"AI响应验证失败: {validation_result['validation_result']['issues_found']}")

        # 10. 返回验证和可能纠正后的响应
        final_response = validation_result["final_response"]

        # 11. 检查角色漂移
        if self.drift_prevention.detect_drift(member_id, final_response):
            # 如果检测到漂移，尝试修正
            final_response = await self._correct_response_if_drifting(
                member_id, final_response, secure_prompt
            )

        return final_response

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
                max_tokens=300,
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

    def _post_process_response(self, response: str) -> str:
        """后处理AI响应，使其更自然"""
        # 去除过度的格式化标记
        import re
        
        # 移除过多的星号、井号等格式符号
        processed = re.sub(r'\*{2,}', '', response)  # 移除多余的**
        processed = re.sub(r'#{1,}', '', processed)   # 移除多余的#
        processed = re.sub(r'^\s*[-*]\s*', '', processed, flags=re.MULTILINE)  # 移除列表符号
        
        # 限制重复的换行符
        processed = re.sub(r'\n{3,}', '\n\n', processed)
        
        # 修剪首尾空白
        processed = processed.strip()
        
        # 确保不超过最大长度
        if len(processed) > 200:
            processed = processed[:200] + "..."
        
        return processed

    def validate_group_exists(self, group_id: int) -> bool:
        """验证群组是否存在"""
        group = self.db.query(AiChatGroup).filter(
            AiChatGroup.id == group_id
        ).first()
        
        return group is not None