"""
AI群聊上下文管理系统
负责维护和提供对话上下文
"""

from __future__ import annotations
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.ai_chat import AiGroupMember, AiMessage


class ConversationContextManager:
    def __init__(self, db_session: Session):
        self.db = db_session

    def build_conversation_context(self, group_id: int, limit: int = 15) -> str:
        """构建完整的对话上下文"""
        # 获取最近的对话历史
        messages = self.db.query(AiMessage).filter(
            AiMessage.group_id == group_id
        ).order_by(
            AiMessage.created_at.asc()  # 按时间升序排列
        ).limit(limit).all()

        # 构建格式化的对话历史
        conversation_history = []
        for msg in messages:
            # 检查消息内容是否为None
            if msg.content is None:
                continue  # 跳过内容为None的消息
            
            sender = self.db.query(AiGroupMember).filter(
                AiGroupMember.id == msg.member_id
            ).first()

            sender_name = sender.ai_nickname if (sender and sender.ai_nickname is not None) else "Unknown"
            conversation_history.append(f"{sender_name}: {msg.content}")

        return "\n".join(conversation_history)

    def extract_topic_and_context(self, group_id: int) -> tuple[str, str]:
        """提取当前讨论的主题和上下文"""
        # 获取最近的对话
        recent_messages = self.build_conversation_context(group_id, limit=20)

        # 简单的主题提取（实际应用中可以使用NLP技术）
        lines = recent_messages.split('\n')
        # 假设最近几行包含了当前讨论的主要话题
        topic_context = '\n'.join(lines[-5:]) if len(lines) >= 5 else recent_messages

        # 这里可以加入更复杂的主题识别逻辑
        return self._identify_topic(topic_context), topic_context

    def _identify_topic(self, context: str) -> str:
        """识别对话主题（简化版）"""
        # 实际应用中可以使用NLP技术进行更精确的主题识别
        # 这里只是简单示例
        return context[:100] + "..."  # 截取前100字符作为主题


class SelectiveContextProvider:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.conversation_manager = ConversationContextManager(db_session)

    def provide_context(self, group_id: int, target_member_id: int) -> str:
        """为特定AI提供定制化上下文"""
        # 获取目标AI的信息
        target_member = self.db.query(AiGroupMember).filter(
            AiGroupMember.id == target_member_id
        ).first()

        if not target_member:
            raise ValueError(f"AI成员不存在: {target_member_id}")

        # 获取完整的对话历史
        full_conversation = self.conversation_manager.build_conversation_context(group_id)

        # 获取当前讨论的主题
        current_topic, topic_context = self.conversation_manager.extract_topic_and_context(group_id)

        # 识别与目标AI相关的消息
        relevant_messages = self._identify_relevant_messages(
            group_id, target_member, limit=10
        )

        # 构建最终上下文
        context_parts = []

        # 1. 当前讨论主题（最重要）
        context_parts.append(f"当前讨论主题：{current_topic}")

        # 2. 与目标AI相关的消息
        if relevant_messages:
            context_parts.append("\n与你相关的消息：")
            for msg in relevant_messages:
                sender = self.db.query(AiGroupMember).filter(
                    AiGroupMember.id == msg.member_id
                ).first()
                sender_name = sender.ai_nickname if (sender and sender.ai_nickname is not None) else "Unknown"
                context_parts.append(f"{sender_name}: {msg.content}")

        # 3. 最新的对话片段（提供即时上下文）
        recent_messages = self._get_recent_messages(group_id, limit=5)
        if recent_messages:
            context_parts.append("\n最新对话：")
            for msg in recent_messages:
                sender = self.db.query(AiGroupMember).filter(
                    AiGroupMember.id == msg.member_id
                ).first()
                sender_name = sender.ai_nickname if (sender and sender.ai_nickname is not None) else "Unknown"
                context_parts.append(f"{sender_name}: {msg.content}")

        return "\n".join(context_parts)

    def _identify_relevant_messages(self, group_id: int, target_member: AiGroupMember, limit: int):
        """识别与目标AI相关的消息"""
        all_messages = self.db.query(AiMessage).filter(
            AiMessage.group_id == group_id
        ).order_by(
            AiMessage.created_at.desc()
        ).limit(limit * 2).all()

        relevant_messages = []
        for msg in reversed(all_messages):
            # 检查是否提及目标AI - 需要确保字段不是None
            if (target_member.ai_nickname is not None and 
                ((msg.content is not None and f"@{target_member.ai_nickname}" in msg.content) or
                 (msg.content is not None and target_member.ai_nickname in msg.content) or
                 msg.member_id == target_member.id)):
                relevant_messages.append(msg)

        return relevant_messages[-limit:] if len(relevant_messages) > limit else relevant_messages

    def _get_recent_messages(self, group_id: int, limit: int):
        """获取最新的消息"""
        return self.db.query(AiMessage).filter(
            AiMessage.group_id == group_id
        ).order_by(
            AiMessage.created_at.desc()
        ).limit(limit).all()[::-1]  # 反转以获得正确的时间顺序


def build_context_aware_prompt(
    character_prompt: str,
    conversation_context: str,
    target_member_nickname: str,
    target_member_personality: str,
    target_member_stance: str
) -> str:
    """构建具有上下文感知能力的提示"""

    # 确保所有参数都不是None
    target_member_nickname = target_member_nickname if target_member_nickname is not None else "Unknown"
    target_member_personality = target_member_personality if target_member_personality is not None else "Unknown"
    target_member_stance = target_member_stance if target_member_stance is not None else "Unknown"

    return f"""
{character_prompt}

重要提醒：
1. 你叫{target_member_nickname}，请始终以你的身份回应。
2. 你的人格特点是：{target_member_personality}。
3. 你对这个话题的立场是：{target_member_stance}。
4. 以下是当前对话的上下文，请根据上下文进行回应，不要脱离话题：
{conversation_context}

请基于以上信息进行回应，确保你的回答与对话上下文相关且符合你的角色特征。
"""