"""
AI相关性检测服务
用于检测消息与特定AI的相关性，决定是否触发AI回应
"""

from __future__ import annotations
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.ai_chat import AiGroupMember, AiMessage


class MessageRelevanceDetector:
    def __init__(self, db_session: Session):
        self.db = db_session

    def detect_relevance(self, message: AiMessage, target_member: AiGroupMember) -> Dict[str, Any]:
        """检测消息与目标AI的相关性"""
        relevance_scores = {
            'direct_mention': self._check_direct_mention(message, target_member),
            'indirect_reference': self._check_indirect_reference(message, target_member),
            'topic_alignment': self._check_topic_alignment(message, target_member),
            'role_relevance': self._check_role_relevance(message, target_member),
            'stance_relevance': self._check_stance_relevance(message, target_member)
        }

        # 计算总体相关性分数
        total_score = sum(relevance_scores.values())

        return {
            'scores': relevance_scores,
            'total_score': total_score,
            'is_relevant': total_score > 0.5,  # 阈值可调整
            'relevance_type': self._determine_relevance_type(relevance_scores)
        }

    def _check_direct_mention(self, message: AiMessage, target_member: AiGroupMember) -> float:
        """检查是否直接提及目标AI"""
        # 检查@提及 - 需要确保 ai_nickname 不为 None
        if target_member.ai_nickname is not None and f"@{target_member.ai_nickname}" in message.content:
            return 1.0  # 完全相关

        # 检查不带@的直接称呼 - 需要确保 ai_nickname 不为 None
        if target_member.ai_nickname is not None and target_member.ai_nickname in message.content:
            return 0.8  # 高度相关

        return 0.0  # 无关

    def _check_indirect_reference(self, message: AiMessage, target_member: AiGroupMember) -> float:
        """检查间接引用或暗示"""
        # 检查是否提到目标AI的立场关键词
        if (target_member.initial_stance is not None and target_member.initial_stance.strip() and
            message.content is not None and target_member.initial_stance in message.content):
            return 0.6  # 中等相关

        # 检查是否提到目标AI的性格特征
        if (target_member.personality is not None and target_member.personality.strip() and
            message.content is not None and target_member.personality in message.content):
            return 0.5  # 中等相关

        # 检查是否在回复目标AI的上一条消息
        previous_message = self._get_previous_message(message)
        if previous_message is not None and previous_message.member_id == target_member.id:
            return 0.7  # 高相关（回复该AI的消息）

        return 0.0

    def _check_topic_alignment(self, message: AiMessage, target_member: AiGroupMember) -> float:
        """检查话题是否与目标AI的专业领域或兴趣相关"""
        # 检查消息内容是否涉及目标AI的立场话题
        if (target_member.initial_stance is not None and target_member.initial_stance.strip() and
            message.content is not None and message.content.strip()):
            stance_keywords = target_member.initial_stance.split()
            message_words = message.content.lower().split()

            matching_keywords = [kw for kw in stance_keywords if kw.lower() in message_words]
            if matching_keywords:
                return min(len(matching_keywords) / len(stance_keywords), 1.0) * 0.5

        return 0.0

    def _check_role_relevance(self, message: AiMessage, target_member: AiGroupMember) -> float:
        """检查消息是否与目标AI的角色相关"""
        # 这里可以根据AI的personality字段推断角色
        personality_lower = target_member.personality.lower() if target_member.personality is not None and target_member.personality.strip() else ""
        message_content = message.content.lower() if message.content is not None else ""

        # 检查消息是否涉及需要特定角色回应的情况
        if (message.content is not None and "问题" in message_content and "专家" in personality_lower):
            return 0.6
        elif (message.content is not None and "辩论" in message_content and "批判" in personality_lower):
            return 0.6
        elif (message.content is not None and "建议" in message_content and "指导" in personality_lower):
            return 0.6

        return 0.0

    def _check_stance_relevance(self, message: AiMessage, target_member: AiGroupMember) -> float:
        """检查消息是否与目标AI的立场相关"""
        if target_member.initial_stance is None or not target_member.initial_stance.strip():
            return 0.0

        # 检查消息是否涉及目标AI的立场话题
        stance_keywords = target_member.initial_stance.lower().split()
        message_lower = message.content.lower() if message.content is not None else ""

        # 计算立场相关性
        stance_matches = sum(1 for kw in stance_keywords if kw in message_lower)
        if stance_matches > 0:
            return min(stance_matches / len(stance_keywords), 1.0) * 0.7

        return 0.0

    def _get_previous_message(self, current_message: AiMessage) -> Optional[AiMessage]:
        """获取当前消息的前一条消息"""
        # 检查 current_message.created_at 是否为 None
        if current_message.created_at is None:
            return None
            
        prev_message = self.db.query(AiMessage).filter(
            AiMessage.group_id == current_message.group_id,
            AiMessage.created_at < current_message.created_at
        ).order_by(
            AiMessage.created_at.desc()
        ).first()

        return prev_message

    def _determine_relevance_type(self, scores: Dict[str, float]) -> str:
        """确定相关性类型"""
        if scores['direct_mention'] > 0:
            return 'direct_mention'
        elif scores['indirect_reference'] > 0:
            return 'indirect_reference'
        elif scores['topic_alignment'] > 0:
            return 'topic_aligned'
        elif scores['role_relevance'] > 0:
            return 'role_relevant'
        elif scores['stance_relevance'] > 0:
            return 'stance_relevant'
        else:
            return 'not_relevant'


class SmartTriggerDetector:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.relevance_detector = MessageRelevanceDetector(db_session)

    def should_trigger_ai(self, group_id: int, target_member_id: int, trigger_message: str = None) -> bool:
        """判断是否应该触发指定AI"""
        target_member = self.db.query(AiGroupMember).filter(
            AiGroupMember.id == target_member_id
        ).first()

        if not target_member:
            return False

        # 验证AI成员的必要字段 - 使用 is not None 来避免SQLAlchemy错误
        if (target_member.ai_nickname is None or
            target_member.personality is None or
            target_member.initial_stance is None or
            not target_member.ai_nickname.strip() or  # 检查是否为空字符串
            not target_member.personality.strip() or
            (target_member.initial_stance is not None and not target_member.initial_stance.strip())):  # initial_stance可以为空
            return False

        # 如果有显式的触发消息，直接检查相关性
        if trigger_message is not None:  # 明确检查是否为None
            # 创建一个虚拟消息对象来测试相关性
            mock_message = AiMessage(
                group_id=group_id,
                member_id=-1,  # 临时值
                content=trigger_message
            )
            relevance_result = self.relevance_detector.detect_relevance(mock_message, target_member)
            return relevance_result['is_relevant']

        # 检查最近的消息是否与目标AI相关
        recent_messages = self._get_unprocessed_messages(group_id, target_member_id)

        for msg in recent_messages:
            relevance_result = self.relevance_detector.detect_relevance(msg, target_member)
            if relevance_result['is_relevant']:
                return True

        return False

    def _get_unprocessed_messages(self, group_id: int, target_member_id: int):
        """获取未处理的消息（实际应用中可能需要一个已处理消息的标记）"""
        # 简化实现：获取最近5条消息
        return self.db.query(AiMessage).filter(
            AiMessage.group_id == group_id
        ).order_by(
            AiMessage.created_at.desc()
        ).limit(5).all()

    def get_trigger_reasons(self, group_id: int, target_member_id: int) -> list:
        """获取触发AI的原因"""
        target_member = self.db.query(AiGroupMember).filter(
            AiGroupMember.id == target_member_id
        ).first()

        if not target_member:
            return []

        recent_messages = self._get_unprocessed_messages(group_id, target_member_id)
        trigger_reasons = []

        for msg in recent_messages:
            relevance_result = self.relevance_detector.detect_relevance(msg, target_member)
            if relevance_result['is_relevant']:
                sender = self.db.query(AiGroupMember).filter(
                    AiGroupMember.id == msg.member_id
                ).first()

                reason = {
                    'message': msg.content,
                    'sender': sender.ai_nickname if (sender and sender.ai_nickname is not None) else 'Unknown',
                    'relevance_type': relevance_result['relevance_type'],
                    'score': relevance_result['total_score']
                }
                trigger_reasons.append(reason)

        return trigger_reasons