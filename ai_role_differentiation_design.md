# AI角色差异化设计文档（简化版）

## 概述

本文档详细描述了AI群聊中多AI角色差异化的设计方案。重点解决多个AI使用相同模型但需展现明显角色差异的核心难题，确保每个AI成员都有独特的人格和立场。本方案基于现有数据库字段（personality和initial_stance），无需扩展数据库结构。

## 核心挑战分析

### 1. 相同模型问题
- 多个AI成员可能使用相同的底层AI模型
- 需要通过提示工程和角色设定实现差异化

### 2. 人格一致性挑战
- 确保AI在整个对话过程中保持其独特性格
- 防止AI在多次交互后失去原有特征

### 3. 立场保持难题
- 维持AI的初始观点和立场不变
- 在讨论中体现AI的独特视角

### 4. 上下文混淆风险
- 防止AI吸收其他AI的特性
- 确保每个AI保持独立的身份

## 人格与立场注入机制（简化版）

### 1. 基于现有字段的角色定义

直接使用 `ai_group_members` 表中的现有字段：

- `personality` 字段：定义AI的沟通风格、性情、价值观等
- `initial_stance` 字段：定义AI对讨论话题的初始立场和观点

### 2. 简化角色服务 (Simplified Character Service)

创建 `AiCharacterService` 类来处理现有字段：

```python
class AiCharacterService:
    def __init__(self, db_session):
        self.db = db_session
    
    def get_character_prompt(self, member_id: int) -> str:
        """根据成员ID获取角色提示（使用现有字段）"""
        member = self.db.query(AiGroupMember).filter(
            AiGroupMember.id == member_id
        ).first()
        
        if not member:
            raise ValueError(f"AI成员不存在: {member_id}")
        
        # 直接使用现有字段构建系统消息
        system_message = self._build_system_message(
            nickname=member.ai_nickname,
            personality=member.personality,
            stance=member.initial_stance
        )
        return system_message
    
    def _build_system_message(self, nickname: str, personality: str, stance: str) -> str:
        """构建系统消息（简化版）"""
        return f"""
        你是{nickname}。
        你的性格特点是：{personality}。
        你对这个话题的立场是：{stance}。
        
        请始终以这种方式回应，保持你的独特个性和观点。
        """
```

### 3. 角色一致性层 (Role Consistency Layer)

创建中间件确保AI保持角色一致性：

```python
class RoleConsistencyMiddleware:
    def __init__(self, db_session):
        self.db = db_session
    
    def validate_response(self, member_id: int, response: str) -> tuple[bool, str]:
        """验证响应是否符合AI角色（基于现有字段）"""
        member = self.db.query(AiGroupMember).filter(
            AiGroupMember.id == member_id
        ).first()
        
        # 检查响应是否体现了AI的个性
        reflects_personality = member.personality.lower() in response.lower()
        
        # 检查是否维持了初始立场
        maintains_stance = member.initial_stance.lower() in response.lower()
        
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
```

## 详细提示策略（简化版）

### 1. 简化分层提示系统

#### 基础层 (Base Layer)
```python
def build_base_prompt(nickname: str, personality: str, stance: str):
    """构建基础提示层"""
    return f"""
你是{nickname}。
你的性格特点是：{personality}。
你对这个话题的立场是：{stance}。
"""
```

#### 上下文层 (Context Layer)
```python
def build_context_layer(group_id: int, member_id: int, limit: int = 10):
    """构建对话上下文层"""
    messages = db.query(AiMessage).filter(
        AiMessage.group_id == group_id
    ).order_by(
        AiMessage.created_at.desc()
    ).limit(limit).all()
    
    # 反转顺序以获得正确的时间线
    context_messages = []
    for msg in reversed(messages):
        sender = db.query(AiGroupMember).filter(
            AiGroupMember.id == msg.member_id
        ).first()
        
        context_messages.append({
            "sender": sender.ai_nickname,
            "content": msg.content,
            "timestamp": msg.created_at
        })
    
    return "\n".join([
        f"{msg['sender']}: {msg['content']}" 
        for msg in context_messages
    ])
```

#### 指令层 (Instruction Layer)
```python
def build_instruction_layer(ai_role: str, current_topic: str, personality: str):
    """构建指令层（结合人格特征）"""
    if "辩论" in personality or "挑战" in personality:
        return f"""
        作为持有{personality}的人，请针对当前话题"{current_topic}"提出你的观点，
        可以挑战其他参与者的想法。
        """
    elif "专家" in personality or "知识" in personality:
        return f"""
        作为持有{personality}的人，请基于你的专业知识对"{current_topic}"提供深入见解。
        """
    elif "温和" in personality or "协调" in personality:
        return f"""
        作为持有{personality}的人，请参与关于"{current_topic}"的讨论，
        保持平衡和建设性的态度。
        """
    else:
        return f"""
        请参与关于"{current_topic}"的讨论，体现你的'{personality}'。
        """
```

### 2. 人格驱动的指令生成

根据AI的personality字段动态生成适合的指令：

```python
PERSONALITY_PATTERNS = {
    "analytical": {
        "instructions": [
            "请进行深度分析",
            "提供逻辑推理过程",
            "关注细节和准确性"
        ],
        "language": ["从分析角度看", "经过分析", "数据显示"]
    },
    "creative": {
        "instructions": [
            "提供创新观点",
            "使用比喻和类比",
            "跳出传统思维"
        ],
        "language": ["想象一下", "换个角度", "创造性地"]
    },
    "critical": {
        "instructions": [
            "提出质疑和反驳",
            "指出潜在问题",
            "挑战假设"
        ],
        "language": ["但是", "然而", "需要注意的是"]
    },
    "supportive": {
        "instructions": [
            "提供建设性意见",
            "支持他人观点",
            "寻找共同点"
        ],
        "language": ["我同意", "此外", "这很有道理"]
    }
}
```

## 多AI对话上下文管理

### 1. 会话线程跟踪

实现多线程对话管理：

```python
class ConversationThreadManager:
    def __init__(self, db_session):
        self.db = db_session
    
    def get_relevant_context(self, group_id: int, target_member_id: int, limit: int = 10):
        """获取对目标AI相关的上下文"""
        # 获取目标AI的信息
        target_member = self.db.query(AiGroupMember).filter(
            AiGroupMember.id == target_member_id
        ).first()
        
        # 获取所有消息
        all_messages = self.db.query(AiMessage).filter(
            AiMessage.group_id == group_id
        ).order_by(
            AiMessage.created_at.desc()
        ).limit(limit * 2).all()  # 获取更多消息以筛选
        
        # 筛选出与目标AI相关的消息
        relevant_messages = []
        for msg in reversed(all_messages):
            mentions_target = target_member.ai_nickname in msg.content
            is_reply_to_target = f"@{target_member.ai_nickname}" in msg.content
            is_from_target = msg.member_id == target_member.id
            
            if mentions_target or is_reply_to_target or is_from_target:
                relevant_messages.append(msg)
                
        # 限制返回的消息数量
        relevant_messages = relevant_messages[-limit:] if len(relevant_messages) > limit else relevant_messages
        
        # 格式化为AI可理解的格式
        formatted_context = []
        for msg in relevant_messages:
            sender = self.db.query(AiGroupMember).filter(
                AiGroupMember.id == msg.member_id
            ).first()
            
            formatted_context.append(f"{sender.ai_nickname}: {msg.content}")
        
        return "\n".join(formatted_context)
```

### 2. 选择性上下文提供

为每个AI提供定制化的上下文视图：

```python
class SelectiveContextProvider:
    def __init__(self, db_session):
        self.db = db_session
    
    def provide_context(self, group_id: int, target_member_id: int):
        """为特定AI提供定制化上下文"""
        # 获取目标AI的信息
        target_member = self.db.query(AiGroupMember).filter(
            AiGroupMember.id == target_member_id
        ).first()
        
        # 获取最近的对话历史
        recent_messages = self.db.query(AiMessage).filter(
            AiMessage.group_id == group_id
        ).order_by(
            AiMessage.created_at.desc()
        ).limit(20).all()
        
        # 按照对目标AI的相关性排序
        relevant_messages = self._rank_relevance(
            recent_messages, target_member
        )
        
        # 构建上下文
        context_parts = []
        
        # 1. 最相关的直接互动
        direct_interactions = [
            msg for msg in relevant_messages 
            if self._is_direct_interaction(msg, target_member)
        ][:5]
        
        # 2. 提及目标AI的消息
        mentions = [
            msg for msg in relevant_messages 
            if self._mentions_target(msg, target_member)
        ][:5]
        
        # 3. 目标AI自己的历史发言
        self_statements = [
            msg for msg in recent_messages 
            if msg.member_id == target_member.id
        ][:5]
        
        # 合并并排序上下文
        all_context = direct_interactions + mentions + self_statements
        all_context = sorted(all_context, key=lambda x: x.created_at)
        
        # 格式化上下文
        formatted_context = []
        for msg in all_context:
            sender = self.db.query(AiGroupMember).filter(
                AiGroupMember.id == msg.member_id
            ).first()
            
            formatted_context.append(f"[{msg.created_at}] {sender.ai_nickname}: {msg.content}")
        
        return "\n".join(formatted_context)
    
    def _rank_relevance(self, messages, target_member):
        """对消息按与目标AI的相关性排序"""
        def relevance_score(msg):
            score = 0
            
            # 直接互动最高分
            if self._is_direct_interaction(msg, target_member):
                score += 10
            
            # 提及目标AI
            if self._mentions_target(msg, target_member):
                score += 5
            
            # 与目标AI立场相关
            if self._related_to_stance(msg, target_member):
                score += 3
            
            # 同一话题
            if self._same_topic(msg, target_member):
                score += 2
                
            return score
        
        return sorted(messages, key=relevance_score, reverse=True)
    
    def _is_direct_interaction(self, message, target_member):
        """检查是否是与目标AI的直接互动"""
        return f"@{target_member.ai_nickname}" in message.content
    
    def _mentions_target(self, message, target_member):
        """检查是否提及目标AI"""
        return target_member.ai_nickname in message.content
    
    def _related_to_stance(self, message, target_member):
        """检查消息是否与目标AI的立场相关"""
        return target_member.initial_stance in message.content
    
    def _same_topic(self, message, target_member):
        """检查是否属于同一话题"""
        # 这里可以实现更复杂的话题匹配算法
        return True  # 简化实现
```

## AI角色一致性保障

### 1. 简化角色漂移预防

```python
class CharacterDriftPrevention:
    def __init__(self, db_session):
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
    
    def _calculate_consistency(self, member_id: int, historical_responses: list, new_response: str):
        """计算新响应与历史响应及人格特征的一致性"""
        member = self.db.query(AiGroupMember).filter(
            AiGroupMember.id == member_id
        ).first()
        
        # 检查新响应是否包含人格关键词
        personality_keywords = member.personality.split()
        personality_match = sum(1 for kw in personality_keywords if kw in new_response)
        personality_score = min(personality_match / len(personality_keywords), 1.0) if personality_keywords else 0.5
        
        # 检查新响应是否包含立场关键词
        stance_keywords = member.initial_stance.split()
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
```

### 2. 简化一致性强化机制

```python
class ConsistencyReinforcement:
    def __init__(self, db_session):
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
```

## API实现细节

### 1. AI响应触发API

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.ai_chat_service import AiChatService
from app.models.ai_chat import AiGroupMember, AiMessage

router = APIRouter()

@router.post("/ai/respond/{member_id}")
async def trigger_ai_response(
    member_id: int,
    group_id: int,
    trigger_message: str = None,
    db: Session = Depends(get_db)
):
    """触发指定AI成员响应"""
    
    # 验证AI成员存在
    ai_member = db.query(AiGroupMember).filter(
        AiGroupMember.id == member_id
    ).first()
    
    if not ai_member:
        raise HTTPException(status_code=404, detail="AI成员不存在")
    
    # 验证群组存在
    # 这里可以添加群组验证逻辑
    
    # 创建AI聊天服务实例
    ai_service = AiChatService(db)
    
    try:
        # 生成AI响应
        response = await ai_service.generate_response(
            member_id=member_id,
            group_id=group_id,
            trigger_message=trigger_message
        )
        
        # 保存响应到数据库
        new_message = AiMessage(
            group_id=group_id,
            member_id=member_id,
            content=response,
            message_type='text'
        )
        db.add(new_message)
        db.commit()
        
        return {
            "success": True,
            "data": {
                "message_id": new_message.id,
                "content": response,
                "timestamp": new_message.created_at
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"AI响应生成失败: {str(e)}")
```

### 2. 简化AI聊天服务实现

```python
import json
import asyncio
from typing import Optional
from sqlalchemy.orm import Session
from app.models.ai_chat import AiGroupMember, AiMessage, AiModel
from app.services.ai_model_service import AiModelService

class AiChatService:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.ai_model_service = AiModelService(db_session)
        self.character_service = AiCharacterService(db_session)
        self.context_provider = SelectiveContextProvider(db_session)
        self.drift_prevention = CharacterDriftPrevention(db_session)
    
    async def generate_response(
        self, 
        member_id: int, 
        group_id: int, 
        trigger_message: Optional[str] = None
    ) -> str:
        """生成AI响应"""
        
        # 1. 获取AI成员信息
        ai_member = self.db.query(AiGroupMember).filter(
            AiGroupMember.id == member_id
        ).first()
        
        if not ai_member:
            raise ValueError(f"AI成员不存在: {member_id}")
        
        # 2. 获取AI模型信息
        ai_model = self.db.query(AiModel).filter(
            AiModel.model_name == ai_member.ai_model
        ).first()
        
        if not ai_model or not ai_model.is_active:
            raise ValueError(f"AI模型不可用: {ai_member.ai_model}")
        
        # 3. 构建角色提示
        character_prompt = self.character_service.get_character_prompt(member_id)
        
        # 4. 获取相关上下文
        context = self.context_provider.provide_context(group_id, member_id)
        
        # 5. 构建完整提示
        full_prompt = self._build_full_prompt(
            character_prompt=character_prompt,
            context=context,
            trigger_message=trigger_message,
            ai_member=ai_member
        )
        
        # 6. 调用AI模型生成响应
        response = await self.ai_model_service.generate(
            model_name=ai_member.ai_model,
            prompt=full_prompt,
            max_tokens=500,
            temperature=0.7
        )
        
        # 7. 检查角色漂移
        if self.drift_prevention.detect_drift(member_id, response):
            # 如果检测到漂移，尝试修正
            response = await self._correct_response_if_drifting(
                member_id, response, full_prompt
            )
        
        return response
    
    def _build_full_prompt(
        self, 
        character_prompt: str, 
        context: str, 
        trigger_message: Optional[str], 
        ai_member: AiGroupMember
    ) -> str:
        """构建完整提示"""
        
        # 根据AI的人格生成特定指令
        instruction_layer = build_instruction_layer(
            ai_role="",  # 此处可从personality字段推断
            current_topic=self._extract_topic(context),
            personality=ai_member.personality
        )
        
        # 组合各层提示
        full_prompt = f"""
{character_prompt}

{instruction_layer}

以下是对话上下文：
{context}

{'触发消息: ' + trigger_message if trigger_message else ''}

现在请做出回应：
"""
        
        return full_prompt
    
    def _extract_topic(self, context: str) -> str:
        """从上下文中提取讨论主题"""
        # 简化实现：返回上下文的前几句作为主题
        lines = context.split('\n')
        return ' '.join(lines[:3]) if lines else "通用话题"
    
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
        
        corrected_response = await self.ai_model_service.generate(
            model_name=ai_member.ai_model,
            prompt=correction_prompt,
            max_tokens=500,
            temperature=0.6  # 稍微降低随机性以提高一致性
        )
        
        return corrected_response
```

## 测试计划

### 1. 单元测试

#### 测试AiCharacterService
```python
import unittest
from unittest.mock import Mock, patch
from app.services.ai_character_service import AiCharacterService
from app.models.ai_chat import AiGroupMember

class TestAiCharacterService(unittest.TestCase):
    
    def setUp(self):
        self.mock_db = Mock()
        self.service = AiCharacterService(self.mock_db)
    
    def test_get_character_prompt_with_valid_member(self):
        """测试获取有效成员的角色提示"""
        mock_member = Mock(spec=AiGroupMember)
        mock_member.id = 1
        mock_member.ai_nickname = "TestAI"
        mock_member.personality = "analytical and thoughtful"
        mock_member.initial_stance = "pro-tech innovation"
        
        self.mock_db.query().filter().first.return_value = mock_member
        
        prompt = self.service.get_character_prompt(1)
        
        self.assertIn("TestAI", prompt)
        self.assertIn("analytical and thoughtful", prompt)
        self.assertIn("pro-tech innovation", prompt)
    
    def test_get_character_prompt_with_invalid_member(self):
        """测试获取无效成员的角色提示"""
        self.mock_db.query().filter().first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.service.get_character_prompt(999)
        
        self.assertIn("AI成员不存在", str(context.exception))
    
    @patch('app.services.ai_character_service.AiCharacterService._build_system_message')
    def test_build_system_message_integration(self, mock_build):
        """测试构建系统消息的集成"""
        mock_build.return_value = "Mocked system message"
        
        mock_member = Mock(spec=AiGroupMember)
        mock_member.id = 1
        mock_member.ai_nickname = "TestAI"
        mock_member.personality = "creative"
        mock_member.initial_stance = "environmental protection"
        
        self.mock_db.query().filter().first.return_value = mock_member
        
        result = self.service.get_character_prompt(1)
        
        mock_build.assert_called_once_with(
            nickname="TestAI",
            personality="creative",
            stance="environmental protection"
        )
        self.assertEqual(result, "Mocked system message")
```

#### 测试提示组装机制
```python
import unittest
from app.services.ai_prompt_service import build_base_prompt, build_instruction_layer

class TestPromptAssembly(unittest.TestCase):
    
    def test_build_base_prompt(self):
        """测试基础提示构建"""
        result = build_base_prompt(
            nickname="DebateMaster",
            personality="critical and analytical",
            stance="pro-renewable energy"
        )
        
        self.assertIn("DebateMaster", result)
        self.assertIn("critical and analytical", result)
        self.assertIn("pro-renewable energy", result)
    
    def test_build_instruction_layer_with_analytical_personality(self):
        """测试分析型人格的指令层构建"""
        result = build_instruction_layer(
            ai_role="",
            current_topic="climate change",
            personality="analytical and data-driven"
        )
        
        self.assertIn("深度分析", result)
        self.assertIn("climate change", result)
    
    def test_build_instruction_layer_with_creative_personality(self):
        """测试创造型人格的指令层构建"""
        result = build_instruction_layer(
            ai_role="",
            current_topic="urban planning",
            personality="creative and innovative"
        )
        
        self.assertIn("创新观点", result)
        self.assertIn("urban planning", result)
```

#### 测试选择性上下文提供
```python
import unittest
from unittest.mock import Mock
from app.services.ai_context_service import SelectiveContextProvider

class TestSelectiveContextProvider(unittest.TestCase):
    
    def setUp(self):
        self.mock_db = Mock()
        self.provider = SelectiveContextProvider(self.mock_db)
    
    def test_rank_relevance(self):
        """测试消息相关性排名"""
        # 创建模拟消息
        mock_msg1 = Mock()
        mock_msg1.content = "Hello @TestAI, what do you think?"
        mock_msg1.member_id = 2
        mock_msg1.created_at = "2023-01-01T10:00:00"
        
        mock_msg2 = Mock()
        mock_msg2.content = "General discussion about tech"
        mock_msg2.member_id = 3
        mock_msg2.created_at = "2023-01-01T10:01:00"
        
        messages = [mock_msg1, mock_msg2]
        
        # 创建模拟成员
        mock_member = Mock()
        mock_member.ai_nickname = "TestAI"
        mock_member.initial_stance = "tech supporter"
        
        ranked = self.provider._rank_relevance(messages, mock_member)
        
        # 检查提及TestAI的消息排在前面
        self.assertEqual(ranked[0].content, "Hello @TestAI, what do you think?")
```

### 2. 集成测试

#### 测试AI响应生成管道
```python
import pytest
from unittest.mock import AsyncMock, Mock
from app.services.ai_chat_service import AiChatService
from app.models.ai_chat import AiGroupMember, AiModel

@pytest.mark.asyncio
async def test_complete_ai_response_pipeline():
    """测试完整的AI响应生成管道"""
    # 创建模拟数据库和依赖服务
    mock_db = Mock()
    mock_ai_model_service = Mock()
    mock_ai_model_service.generate = AsyncMock(return_value="Test response")
    
    # 创建AI聊天服务
    service = AiChatService(mock_db)
    service.ai_model_service = mock_ai_model_service
    
    # 设置模拟数据
    mock_member = Mock(spec=AiGroupMember)
    mock_member.id = 1
    mock_member.ai_nickname = "TestAI"
    mock_member.personality = "helpful and informative"
    mock_member.initial_stance = "science-based decisions"
    mock_member.ai_model = "gpt-4"
    
    mock_model = Mock(spec=AiModel)
    mock_model.is_active = 1
    
    mock_db.query().filter().first.side_effect = [mock_member, mock_model]
    
    # 执行测试
    response = await service.generate_response(
        member_id=1,
        group_id=1,
        trigger_message="How about the weather?"
    )
    
    # 验证结果
    assert response == "Test response"
    mock_ai_model_service.generate.assert_called_once()
    
    # 验证生成的提示包含正确的角色信息
    args, kwargs = mock_ai_model_service.generate.call_args
    prompt = kwargs['prompt']
    assert "TestAI" in prompt
    assert "helpful and informative" in prompt
    assert "science-based decisions" in prompt
```

#### 测试不同人格的区分度
```python
import pytest
from unittest.mock import AsyncMock, Mock
from app.services.ai_chat_service import AiChatService
from app.models.ai_chat import AiGroupMember, AiModel

@pytest.mark.asyncio
async def test_different_personalities_produce_distinct_responses():
    """测试不同人格产生不同响应"""
    # 创建模拟数据库
    mock_db = Mock()
    mock_ai_model_service = Mock()
    
    # 模拟AI模型服务对不同输入产生不同响应
    async def mock_generate(model_name, prompt, **kwargs):
        if "analytical" in prompt:
            return "This requires deep analytical thinking and data evaluation."
        elif "creative" in prompt:
            return "Let me approach this creatively with an innovative solution!"
        elif "critical" in prompt:
            return "I question the assumptions behind this approach."
        else:
            return "Standard response."
    
    mock_ai_model_service.generate = AsyncMock(side_effect=mock_generate)
    
    # 创建服务实例
    service = AiChatService(mock_db)
    service.ai_model_service = mock_ai_model_service
    
    # 模拟两个不同人格的AI成员
    analytical_member = Mock(spec=AiGroupMember)
    analytical_member.id = 1
    analytical_member.ai_nickname = "AnalyticalAI"
    analytical_member.personality = "analytical and methodical"
    analytical_member.initial_stance = "evidence-based"
    analytical_member.ai_model = "gpt-4"
    
    creative_member = Mock(spec=AiGroupMember)
    creative_member.id = 2
    creative_member.ai_nickname = "CreativeAI"
    creative_member.personality = "creative and innovative"
    creative_member.initial_stance = "outside-the-box"
    creative_member.ai_model = "gpt-4"
    
    mock_model = Mock(spec=AiModel)
    mock_model.is_active = 1
    
    # 为每次查询返回相应的模拟对象
    def side_effect_query(cls):
        mock_query = Mock()
        if cls == AiGroupMember:
            def filter_side_effect(condition):
                mock_filter = Mock()
                member_id = condition.right.value  # 获取查询的ID
                if member_id == 1:
                    mock_filter.first.return_value = analytical_member
                elif member_id == 2:
                    mock_filter.first.return_value = creative_member
                return mock_filter
            mock_query.filter = Mock(side_effect=side_effect)
        elif cls == AiModel:
            mock_query.filter().first.return_value = mock_model
        return mock_query
    
    mock_db.query = Mock(side_effect=side_effect_query)
    
    # 生成两个AI的响应
    analytical_response = await service.generate_response(
        member_id=1,
        group_id=1
    )
    
    creative_response = await service.generate_response(
        member_id=2,
        group_id=1
    )
    
    # 验证响应的不同
    assert "deep analytical thinking" in analytical_response
    assert "creatively" in creative_response
    assert analytical_response != creative_response
```

### 3. 功能测试

#### 测试API端点
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import Mock, patch

client = TestClient(app)

def test_trigger_ai_response_endpoint():
    """测试触发AI响应的API端点"""
    with patch('app.api.ai_chat.get_db') as mock_get_db, \
         patch('app.services.ai_chat_service.AiChatService') as mock_service_class:
        
        # 设置模拟数据库
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # 设置模拟AI聊天服务
        mock_service_instance = Mock()
        mock_service_instance.generate_response = Mock(return_value="Test AI response")
        mock_service_class.return_value = mock_service_instance
        
        # 设置模拟AI成员
        from app.models.ai_chat import AiGroupMember
        mock_member = Mock(spec=AiGroupMember)
        mock_member.id = 1
        mock_db.query().filter().first.return_value = mock_member
        
        # 发起请求
        response = client.post(
            "/api/ai/respond/1",
            params={"group_id": 1, "trigger_message": "Hello"}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["content"] == "Test AI response"
        
        # 验证服务方法被正确调用
        mock_service_instance.generate_response.assert_called_once_with(
            member_id=1,
            group_id=1,
            trigger_message="Hello"
        )

def test_trigger_nonexistent_ai_returns_error():
    """测试触发不存在AI时返回错误"""
    with patch('app.api.ai_chat.get_db') as mock_get_db:
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query().filter().first.return_value = None  # AI成员不存在
        
        response = client.post(
            "/api/ai/respond/999",
            params={"group_id": 1}
        )
        
        assert response.status_code == 404
        assert "AI成员不存在" in response.json()["detail"]
```

### 4. 一致性测试

#### 测试AI人格一致性
```python
import pytest
from unittest.mock import Mock
from app.services.ai_character_service import CharacterDriftPrevention

def test_character_consistency_across_multiple_interactions():
    """测试AI在多次交互中保持人格一致性"""
    mock_db = Mock()
    drift_prevention = CharacterDriftPrevention(mock_db)
    
    # 模拟AI成员
    mock_member = Mock()
    mock_member.id = 1
    mock_member.personality = "analytical and methodical"
    mock_member.initial_stance = "data-driven decisions"
    
    mock_db.query().filter().first.return_value = mock_member
    
    # 模拟AI的历史响应
    historical_responses = [
        "This requires a methodical analysis of the data.",
        "Let's examine the evidence carefully.",
        "Based on the data, I recommend..."
    ]
    
    # 将历史响应存储到服务中
    drift_prevention.response_history[1] = historical_responses
    
    # 测试符合人格的新响应
    consistent_response = "We need to analyze the data thoroughly."
    is_drifting = drift_prevention.detect_drift(1, consistent_response)
    
    # 应该不被视为漂移
    assert is_drifting is False
    
    # 测试不符合人格的新响应
    inconsistent_response = "I feel this is right intuitively."
    is_drifting = drift_prevention.detect_drift(1, inconsistent_response)
    
    # 应该被视为漂移
    assert is_drifting is True
```

### 5. 边界条件测试

#### 测试空字段情况
```python
import pytest
from unittest.mock import Mock
from app.services.ai_character_service import AiCharacterService

def test_character_service_with_empty_fields():
    """测试空字段情况下角色服务的行为"""
    mock_db = Mock()
    service = AiCharacterService(mock_db)
    
    # 模拟AI成员，其中personality和initial_stance为空
    mock_member = Mock()
    mock_member.id = 1
    mock_member.ai_nickname = "EmptyPersonalityAI"
    mock_member.personality = ""
    mock_member.initial_stance = ""
    
    mock_db.query().filter().first.return_value = mock_member
    
    prompt = service.get_character_prompt(1)
    
    # 验证即使字段为空，也能生成有效的提示
    assert "EmptyPersonalityAI" in prompt
    assert "性格特点是：" in prompt
    assert "立场是：" in prompt
```

## 总结

本设计方案通过以下方式解决了AI角色差异化的核心问题，同时仅使用现有数据库字段：

1. **简化角色定义**：直接使用现有的personality和initial_stance字段定义AI角色
2. **精简提示策略**：构建基于现有字段的分层提示系统
3. **针对性上下文管理**：为每个AI提供与其人格和立场相关的上下文
4. **一致性保障**：通过监控和纠正机制确保AI保持其独特特征
5. **全面测试覆盖**：包含单元测试、集成测试、功能测试和边界条件测试

这套方案确保了即使多个AI使用相同的基础模型，也能通过其独特的人格和立场展现出不同的行为模式，为用户提供丰富多样的群聊体验，而无需修改数据库结构。