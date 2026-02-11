"""
安全提示词模板服务
提供标准化、安全的提示词模板，防止提示词注入
"""

from typing import Dict, Any, Optional
from app.models.ai_chat import AiGroupMember


class SecurePromptTemplateService:
    """安全提示词模板服务类"""

    def __init__(self):
        # 定义安全的提示词模板
        self.templates = {
            "role_aware": {
                "system": "你是{nickname}，一个AI助手。你的性格特点是：{personality}。你对这个话题的立场是：{stance}。",
                "user_with_context": "当前对话上下文：\n{context}\n\n用户消息：{user_message}\n\n请以你的身份回应，保持你的角色特征。"
            },
            "context_aware": {
                "system": "你是一个AI助手，正在参与群聊。请记住你的角色和立场。",
                "user_with_context": "对话历史：\n{context}\n\n新消息：{user_message}\n\n请回应这个消息，保持你的角色一致性。"
            },
            "mention_triggered": {
                "system": "你是{nickname}，当被@时需要回应。你的性格：{personality}。立场：{stance}。",
                "user_with_context": "群聊内容：\n{context}\n\n有人@你并提问：{user_message}\n\n请回应这个问题，体现你的角色特征。"
            }
        }

    def create_role_aware_prompt(
        self,
        ai_member: AiGroupMember,
        context: str,
        user_message: Optional[str] = None,
        sanitizer=None
    ) -> Dict[str, str]:
        """
        创建基于角色的提示词
        
        Args:
            ai_member: AI成员对象
            context: 对话上下文
            user_message: 用户消息
            sanitizer: 输入净化器实例
            
        Returns:
            包含system和user消息的字典
        """
        # 确保AI成员字段不为None
        nickname = ai_member.ai_nickname or "Unknown"
        personality = ai_member.personality or "Unknown"
        stance = ai_member.initial_stance or "Unknown"
        
        # 净化输入内容
        if sanitizer:
            from app.services.input_sanitizer_service import SanitizationLevel
            context = sanitizer.sanitize_input(context, level=SanitizationLevel.MODERATE)
            if user_message:
                user_message = sanitizer.sanitize_input(user_message, level=SanitizationLevel.MODERATE)
        
        # 如果没有用户消息，只使用上下文
        if not user_message:
            user_content = f"当前对话上下文：\n{context}\n\n请根据上下文进行回应，保持你的角色特征。"
        else:
            user_content = self.templates["role_aware"]["user_with_context"].format(
                context=context,
                user_message=user_message
            )
        
        system_content = self.templates["role_aware"]["system"].format(
            nickname=nickname,
            personality=personality,
            stance=stance
        )
        
        return {
            "system": system_content,
            "user": user_content
        }

    def create_context_aware_prompt(
        self,
        context: str,
        user_message: str,
        sanitizer=None
    ) -> Dict[str, str]:
        """
        创建上下文感知的提示词
        
        Args:
            context: 对话上下文
            user_message: 用户消息
            sanitizer: 输入净化器实例
            
        Returns:
            包含system和user消息的字典
        """
        # 净化输入内容
        if sanitizer:
            from app.services.input_sanitizer_service import SanitizationLevel
            context = sanitizer.sanitize_input(context, level=SanitizationLevel.MODERATE)
            user_message = sanitizer.sanitize_input(user_message, level=SanitizationLevel.MODERATE)
        
        system_content = self.templates["context_aware"]["system"]
        user_content = self.templates["context_aware"]["user_with_context"].format(
            context=context,
            user_message=user_message
        )
        
        return {
            "system": system_content,
            "user": user_content
        }

    def create_mention_triggered_prompt(
        self,
        ai_member: AiGroupMember,
        context: str,
        user_message: str,
        sanitizer=None
    ) -> Dict[str, str]:
        """
        创建@触发的提示词
        
        Args:
            ai_member: AI成员对象
            context: 对话上下文
            user_message: 用户消息
            sanitizer: 输入净化器实例
            
        Returns:
            包含system和user消息的字典
        """
        # 确保AI成员字段不为None
        nickname = ai_member.ai_nickname or "Unknown"
        personality = ai_member.personality or "Unknown"
        stance = ai_member.initial_stance or "Unknown"
        
        # 净化输入内容
        if sanitizer:
            from app.services.input_sanitizer_service import SanitizationLevel
            context = sanitizer.sanitize_input(context, level=SanitizationLevel.MODERATE)
            user_message = sanitizer.sanitize_input(user_message, level=SanitizationLevel.MODERATE)
        
        system_content = self.templates["mention_triggered"]["system"].format(
            nickname=nickname,
            personality=personality,
            stance=stance
        )
        
        user_content = self.templates["mention_triggered"]["user_with_context"].format(
            context=context,
            user_message=user_message
        )
        
        return {
            "system": system_content,
            "user": user_content
        }

    def build_secure_messages(
        self,
        ai_member: AiGroupMember,
        context: str,
        user_message: Optional[str] = None,
        message_type: str = "role_aware",
        sanitizer=None
    ) -> list:
        """
        构建安全的消息列表，适用于大多数AI模型API
        
        Args:
            ai_member: AI成员对象
            context: 对话上下文
            user_message: 用户消息
            message_type: 消息类型
            sanitizer: 输入净化器实例
            
        Returns:
            消息列表，格式为[{"role": ..., "content": ...}, ...]
        """
        if message_type == "context_aware":
            prompt = self.create_context_aware_prompt(context, user_message or "", sanitizer)
        elif message_type == "mention_triggered":
            prompt = self.create_mention_triggered_prompt(ai_member, context, user_message or "", sanitizer)
        else:  # 默认使用role_aware
            prompt = self.create_role_aware_prompt(ai_member, context, user_message, sanitizer)
        
        messages = [
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": prompt["user"]}
        ]
        
        return messages