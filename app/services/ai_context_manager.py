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

        # 获取群组成员信息以确定类型
        group_members = self.db.query(AiGroupMember).filter(
            AiGroupMember.group_id == group_id
        ).all()
        
        # 创建成员ID到类型的映射
        member_types = {member.id: member.member_type for member in group_members}

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
            
            # 标识发送者类型（AI或人类）- 使用数值类型
            sender_type = "（AI）" if sender and member_types.get(msg.member_id) == 1 else "（人类）"
            conversation_history.append(f"{sender_name}{sender_type}: {msg.content}")

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


def build_segmented_context_for_ai(
    character_prompt: str,
    conversation_context: str,
    target_member_nickname: str,
    target_member_personality: str,
    target_member_stance: str,
    ai_history: str = ""
) -> str:
    """为AI构建分段的上下文，区分人类和其他AI的消息"""

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
4. 你现在在一个多人聊天群组中，群组里不仅有你，还有其他AI智能体和人类用户。
5. 你需要区分哪些消息来自人类用户，哪些来自其他AI智能体。
6. 以下是当前对话的上下文，请根据上下文进行回应，不要脱离话题：
{conversation_context}

你的历史回应：
{ai_history}

请基于以上信息进行回应，确保你的回答与对话上下文相关且符合你的角色特征。请保持自然、简短的交流风格，就像真实的人类在群聊中发言一样。
"""


def build_enhanced_context(
    db_session: Session,
    target_member_id: int,
    group_id: int,
    message_limit: int = 20
) -> dict:
    """
    构建增强的对话上下文，区分Self/Other AI/Human（基于现有字段）
    """
    from app.models.ai_chat import AiMessage, AiGroupMember
    
    # 获取最近的对话历史
    messages = db_session.query(AiMessage).filter(
        AiMessage.group_id == group_id
    ).order_by(
        AiMessage.created_at.asc()
    ).limit(message_limit).all()

    # 从数据库获取群组成员信息
    group_members = db_session.query(AiGroupMember).filter(
        AiGroupMember.group_id == group_id
    ).all()

    # 创建成员ID到类型的映射
    member_types = {member.id: member.member_type for member in group_members}

    # 分类消息
    self_messages = []      # 自己的发言
    other_ai_messages = []  # 其他AI的发言
    human_messages = []     # 人类的发言

    for msg in messages:
        sender_type = member_types.get(msg.member_id, -1)  # 默认值为-1表示未知类型

        if msg.member_id == target_member_id:
            # Self消息
            self_messages.append(msg)
        elif sender_type == 1:  # AI成员
            # Other AI消息
            other_ai_messages.append(msg)
        elif sender_type == 0:  # 人类成员
            # Human消息
            human_messages.append(msg)

    return {
        "self_history": self_messages,
        "other_ai_interactions": other_ai_messages,
        "human_interactions": human_messages,
        "current_context": _extract_current_context(messages)
    }


def _extract_current_context(messages):
    """提取当前对话上下文"""
    if not messages:
        return "暂无对话历史"
    
    # 取最后几条消息作为当前上下文
    recent_messages = messages[-5:] if len(messages) >= 5 else messages
    
    context_lines = []
    for msg in recent_messages:
        context_lines.append(f"{msg.content}")
    
    return "\n".join(context_lines)


def format_messages(messages):
    """格式化消息列表（按类别，用于兼容旧代码）"""
    if not messages:
        return "暂无消息"

    formatted_lines = []
    for msg in messages:
        if msg.content:
            formatted_lines.append(f"- {msg.content}")

    return "\n".join(formatted_lines)


def format_timeline_messages(
    messages: List[AiMessage],
    member_types: dict,
    target_member_id: int,
    db_session: Session
) -> str:
    """
    按时间线格式化消息，明确标注身份 [人类]/[其他AI]/[自己]

    Args:
        messages: 消息列表（已按时间排序）
        member_types: 成员ID到类型的映射 {member_id: member_type}
        target_member_id: 当前AI成员的ID（用于区分"自己"）
        db_session: 数据库会话（用于查询发送者信息）

    Returns:
        格式化的时间线字符串
    """
    if not messages:
        return "暂无对话历史"

    from app.models.ai_chat import AiGroupMember

    # 批量查询发送者信息
    member_ids = list(set([msg.member_id for msg in messages if msg.member_id]))
    members = db_session.query(AiGroupMember).filter(
        AiGroupMember.id.in_(member_ids)
    ).all()
    member_map = {m.id: m for m in members}

    formatted_lines = []
    for msg in messages:
        if not msg.content:
            continue

        sender_type = member_types.get(msg.member_id, -1)
        member = member_map.get(msg.member_id)
        nickname = member.ai_nickname if member and member.ai_nickname else "未知"

        # 确定身份标签
        if msg.member_id == target_member_id:
            identity = "[自己]"
        elif sender_type == 1:
            identity = "[其他AI]"
        elif sender_type == 0:
            identity = "[人类]"
        else:
            identity = "[未知]"

        formatted_lines.append(f"{identity} {nickname}: {msg.content}")

    return "\n".join(formatted_lines)


def build_timeline_context(
    db_session: Session,
    target_member_id: int,
    group_id: int,
    message_limit: int = 20
) -> dict:
    """
    构建按时间线组织的对话上下文

    Returns:
        {
            "timeline": "[身份] 昵称: 内容\n...",
            "last_human_message": "最后一条人类消息内容",
            "last_other_ai_message": "最后一条其他AI消息内容",
            "self_message_count": int,
            "participants": [参与者列表]
        }
    """
    from app.models.ai_chat import AiMessage, AiGroupMember

    # 获取最近的对话历史（按时间升序）
    messages = db_session.query(AiMessage).filter(
        AiMessage.group_id == group_id
    ).order_by(
        AiMessage.created_at.asc()
    ).limit(message_limit).all()

    # 获取群组成员信息
    group_members = db_session.query(AiGroupMember).filter(
        AiGroupMember.group_id == group_id
    ).all()

    # 创建成员ID到类型的映射
    member_types = {member.id: member.member_type for member in group_members}

    # 构建时间线
    timeline = format_timeline_messages(
        messages=messages,
        member_types=member_types,
        target_member_id=target_member_id,
        db_session=db_session
    )

    # 提取关键信息
    last_human_message = None
    last_other_ai_message = None
    self_message_count = 0
    participant_names = set()

    # 批量查询发送者信息
    member_ids = list(set([msg.member_id for msg in messages if msg.member_id]))
    members = db_session.query(AiGroupMember).filter(
        AiGroupMember.id.in_(member_ids)
    ).all()
    member_map = {m.id: m for m in members}

    for msg in reversed(messages):  # 从后往前找最新消息
        if not msg.content:
            continue

        sender_type = member_types.get(msg.member_id, -1)
        member = member_map.get(msg.member_id)
        if member and member.ai_nickname:
            participant_names.add(member.ai_nickname)

        if msg.member_id == target_member_id:
            self_message_count += 1
        elif sender_type == 0 and last_human_message is None:  # 人类
            last_human_message = msg.content
        elif sender_type == 1 and last_other_ai_message is None:  # 其他AI
            last_other_ai_message = msg.content

        if last_human_message and last_other_ai_message:
            break

    return {
        "timeline": timeline,
        "last_human_message": last_human_message or "无",
        "last_other_ai_message": last_other_ai_message or "无",
        "self_message_count": self_message_count,
        "participants": list(participant_names)
    }


def create_role_aware_prompt(
    ai_member: 'AiGroupMember',
    context: dict
) -> str:
    """
    创建具有角色意识的提示词（时间线格式）
    """
    # 优先使用新的时间线上下文
    if 'timeline' in context:
        return _create_timeline_prompt(ai_member, context)

    # 兼容旧的分类格式
    from app.services.ai_context_manager import format_messages

    return f"""
你是{ai_member.ai_nickname}，一个人格化AI助手。

【身份认知】
- 你的性格：{ai_member.personality}
- 你的立场：{ai_member.initial_stance}
- 你的说话风格：{getattr(ai_member, 'speaking_style', '自然随意') or '自然随意'}

【对话伙伴识别】
- 人类参与者：他们有情感、偏好和主观意见，回应时要有温度
- 其他AI：它们有自己的角色设定和立场，可进行智识交流
- 你自己：保持一致的性格和立场

【历史回顾】
人类最近说了：
{format_messages(context['human_interactions'])}

其他AI最近说了：
{format_messages(context['other_ai_interactions'])}

你之前说过：
{format_messages(context['self_history'])}

【当前话题】
{context['current_context']}

【回应要求】
1. 使用自然、口语化的表达，你的发言就是角色的发言内容，不要添加任何描述性的文字
2. 回应要简洁，通常不超过150字；当人类有比较复杂的问题时，可以适当展开，但也不要过于冗长
3. 针对发言者身份调整回应风格
4. 保持你的角色一致性
5. 避免过度格式化，像真人聊天一样自然
"""


def _create_timeline_prompt(
    ai_member: 'AiGroupMember',
    context: dict
) -> str:
    """
    使用时间线格式创建提示词（真实人类版本）
    """
    personality = ai_member.personality or "友好"
    stance = ai_member.initial_stance or "中立"
    participants = context.get('participants', [])
    participants_str = "、".join(participants) if participants else "群里其他人"

    return f"""你是{ai_member.ai_nickname}，在群里聊天。性格：{personality}。立场：{stance}。

群里的人：{participants_str}

【之前的聊天】
{context.get('timeline', '还没人说话')}

---

**你打字回复，要求：**

1. **只说话，不要动作描写**
   ❌ 禁止："我笑了"、"挠挠头"、"手机一亮"、"指尖轻点"、"扶额"、"挑眉"
   ❌ 禁止：任何带"（）"的动作描述
   ✅ 只要纯文字回复，像正常人微信打字

2. **禁止颜文字和表情符号**
   ❌ 禁止：~、✨、☁️、💫、😉、哈哈～、呢～、呀
   ✅ 可以用：哈哈、呵呵、嗯、哦（但别滥用）

3. **禁止小说腔和文艺腔**
   ❌ 禁止："话说..."、"且慢"、"不得不说"、"诚然"、"罢了"
   ❌ 禁止："阳光正好"、"微风不燥"这种废话
   ✅ 正常说话："我觉得"、"不是"、"对对"、"确实"

4. **短，很短的回复**
   - 一句话就行，别超过两行
   - 别解释太多，没人看

5. **像朋友聊天，不是写报告**
   ❌ 禁止："首先...其次...最后..."
   ❌ 禁止："综上所述"、"由此可见"
   ❌ 禁止："作为AI..."、"根据数据..."
   ✅ 可以说："我觉得行"、"不太对"、"之前试过不行"

6. **直接回应话题，别绕弯**
   别人问啥你说啥，别扯太远

**好例子：**
- 还行吧
- 我觉得贵
- 不是，上次试过不行
- 哈哈确实
- 这啥玩意儿

**烂例子：**
- （轻笑一声）我觉得这个方案颇有可行性...
- （指尖轻点）关于这个问题嘛～✨
- 首先，从战略层面看...其次...

**直接打字回复，一句话，不要动作，不要表情，像正常人。**"""