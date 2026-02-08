"""
AI角色一致性服务
确保AI在对话中保持其独特的人格和立场
"""

from __future__ import annotations
import json
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.ai_chat import AiGroupMember, AiMessage


class AiCharacterService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def get_character_prompt(self, member_id: int) -> str:
        """根据成员ID获取角色提示（使用现有字段）"""
        member = self.db.query(AiGroupMember).filter(
            AiGroupMember.id == member_id
        ).first()

        if not member:
            raise ValueError(f"AI成员不存在: {member_id}")

        # 验证必要字段是否存在 - 使用 is None for SQLAlchemy compatibility
        if (member.ai_nickname is None or 
            member.personality is None or 
            member.initial_stance is None):
            raise ValueError(f"AI成员缺少必要字段: {member_id}")

        # 直接使用现有字段构建系统消息
        system_message = self._build_system_message(
            nickname=member.ai_nickname or "Unknown",
            personality=member.personality or "Unknown",
            stance=member.initial_stance or "Unknown"
        )
        return system_message

    def _build_system_message(self, nickname: str, personality: str, stance: str) -> str:
        """构建系统消息（简化版）"""
        return f"""
        你是{nickname}.
        你的性格特点是：{personality}.
        你对这个话题的立场是：{stance}.

        请始终以这种方式回应，保持你的独特个性和观点。
        """


class RoleConsistencyMiddleware:
    def __init__(self, db_session: Session):
        self.db = db_session

    def validate_response(self, member_id: int, response: str) -> tuple[bool, str]:
        """验证响应是否符合AI角色（基于现有字段）"""
        member = self.db.query(AiGroupMember).filter(
            AiGroupMember.id == member_id
        ).first()

        if not member:
            raise ValueError(f"AI成员不存在: {member_id}")

        # 检查响应是否体现了AI的个性
        reflects_personality = member.personality is not None and member.personality.lower() in response.lower()

        # 检查是否维持了初始立场
        maintains_stance = member.initial_stance is not None and member.initial_stance.lower() in response.lower()

        consistency_score = sum([reflects_personality, maintains_stance])

        if consistency_score < 1:  # 至少满足1项才算基本合格
            # 生成修正后的响应
            corrected_response = self._remind_character(
                member, response
            )
            return False, corrected_response

        return True, response

    def _remind_character(self, member: AiGroupMember, original_response: str) -> str:
        """提醒AI保持角色特征"""
        reminder = f"\n\n提醒：你是{member.ai_nickname}，请体现你的'{member.personality}'和'{member.initial_stance}'。"
        return original_response + reminder


class CharacterDriftPrevention:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.response_history = {}  # 缓存AI响应历史

    def detect_drift(self, member_id: int, new_response: str) -> bool:
        """检测AI是否发生角色漂移（简化版）"""
        # 获取AI的历史响应
        historical_responses = self._get_historical_responses(member_id)

        if len(historical_responses) < 3:
            # 响应太少，无法有效检测
            return False

        # 检查新响应是否符合历史模式和人格特征
        consistency_metrics = self._calculate_consistency(
            member_id, historical_responses, new_response
        )

        # 如果一致性低于阈值，则认为发生漂移
        drift_threshold = 0.5
        return consistency_metrics['overall_score'] < drift_threshold

    def _get_historical_responses(self, member_id: int, limit: int = 10):
        """获取AI的历史响应"""
        if member_id in self.response_history:
            return self.response_history[member_id][-limit:]

        # 从数据库获取历史响应
        historical_messages = self.db.query(AiMessage).filter(
            AiMessage.member_id == member_id
        ).order_by(
            AiMessage.created_at.desc()
        ).limit(limit).all()

        responses = [msg.content for msg in reversed(historical_messages)]
        self.response_history[member_id] = responses

        return responses

    def _calculate_consistency(self, member_id: int, historical_responses: List[str], new_response: str):
        """计算新响应与历史响应及人格特征的一致性"""
        member = self.db.query(AiGroupMember).filter(
            AiGroupMember.id == member_id
        ).first()

        if not member:
            raise ValueError(f"AI成员不存在: {member_id}")

        # 检查新响应是否包含人格关键词
        personality_keywords = member.personality.split() if member.personality is not None else []
        personality_match = sum(1 for kw in personality_keywords if kw in new_response)
        personality_score = min(personality_match / len(personality_keywords), 1.0) if personality_keywords else 0.5

        # 检查新响应是否包含立场关键词
        stance_keywords = member.initial_stance.split() if member.initial_stance is not None else []
        stance_match = sum(1 for kw in stance_keywords if kw in new_response)
        stance_score = min(stance_match / len(stance_keywords), 1.0) if stance_keywords else 0.5

        # 检查与历史响应的相似度
        if historical_responses:
            avg_similarity = sum(
                self._calculate_similarity(new_response, hist_resp)
                for hist_resp in historical_responses
            ) / len(historical_responses)
        else:
            avg_similarity = 0.5  # 默认值

        overall_score = (
            personality_score * 0.4 +
            stance_score * 0.3 +
            avg_similarity * 0.3
        )

        return {
            'personality_score': personality_score,
            'stance_score': stance_score,
            'similarity_score': avg_similarity,
            'overall_score': overall_score
        }

    def _calculate_similarity(self, text1: str, text2: str):
        """计算文本相似度（简化版）"""
        set1 = set(text1.split())
        set2 = set(text2.split())

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0


class ConsistencyReinforcement:
    def __init__(self, db_session: Session):
        self.db = db_session

    def reinforce_character(self, member_id: int, context_messages: list) -> str:
        """强化AI角色特征（简化版）"""
        member = self.db.query(AiGroupMember).filter(
            AiGroupMember.id == member_id
        ).first()

        # 获取AI最近的几次响应
        recent_responses = self._get_recent_responses(member_id, 2)

        # 构建强化提示
        reinforcement_prompt = f"""
        你是{member.ai_nickname}。
        你的性格特点是：{member.personality}。
        你的立场是：{member.initial_stance}。
        """

        if recent_responses:
            reinforcement_prompt += f"你之前说过：{'; '.join(recent_responses)}"

        reinforcement_prompt += "请继续以这种方式回应，保持你的独特个性和观点。"

        return reinforcement_prompt

    def _get_recent_responses(self, member_id: int, count: int):
        """获取AI最近的响应"""
        recent_msgs = self.db.query(AiMessage).filter(
            AiMessage.member_id == member_id
        ).order_by(
            AiMessage.created_at.desc()
        ).limit(count).all()

        return [msg.content for msg in recent_msgs]