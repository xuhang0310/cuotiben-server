"""
@提及解析服务
用于从消息中提取@的AI成员
"""

import re
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.ai_chat import AiGroupMember


class MentionParser:
    """解析消息中的@提及"""

    def __init__(self, db_session: Session):
        self.db = db_session

    def extract_mentions(self, content: str) -> List[str]:
        """
        从消息内容中提取@的昵称列表

        Args:
            content: 消息内容

        Returns:
            被@的昵称列表（不含@符号）
        """
        if not content:
            return []

        # 匹配 @昵称 格式（支持中文、英文、数字、下划线）
        # @后面跟着一个或多个非空白字符
        pattern = r'@([\u4e00-\u9fa5a-zA-Z0-9_]+)'
        matches = re.findall(pattern, content)

        return matches

    def find_mentioned_members(self, group_id: int, nicknames: List[str]) -> List[AiGroupMember]:
        """
        根据昵称列表查找群组中的AI成员

        Args:
            group_id: 群组ID
            nicknames: 昵称列表

        Returns:
            匹配的AI成员列表（按传入顺序）
        """
        if not nicknames:
            return []

        # 获取群组中所有AI成员
        all_members = self.db.query(AiGroupMember).filter(
            AiGroupMember.group_id == group_id,
            AiGroupMember.member_type == 1  # 只取AI成员
        ).all()

        # 创建昵称到成员的映射（不区分大小写）
        nickname_map = {}
        for member in all_members:
            if member.ai_nickname:
                nickname_map[member.ai_nickname.lower()] = member

        # 按传入顺序查找匹配的成员
        mentioned_members = []
        for nickname in nicknames:
            member = nickname_map.get(nickname.lower())
            if member and member not in mentioned_members:  # 避免重复
                mentioned_members.append(member)

        return mentioned_members

    def parse_mentions_in_group(self, content: str, group_id: int) -> List[AiGroupMember]:
        """
        解析消息在指定群组中的@提及

        Args:
            content: 消息内容
            group_id: 群组ID

        Returns:
            被@的AI成员列表（按@出现的顺序，去重）
        """
        nicknames = self.extract_mentions(content)
        return self.find_mentioned_members(group_id, nicknames)

    def has_mentions(self, content: str) -> bool:
        """检查消息是否包含@提及"""
        return len(self.extract_mentions(content)) > 0
