# AI群聊系统改进方案（修订版）

## 当前问题分析

1. **缺乏多轮对话能力**：AI之间和AI与人类之间的对话缺乏连贯性，每次回复更像是独立的问答而非连续的对话。
2. **过度格式化**：AI回复中使用过多格式化内容，不够自然。
3. **角色区分不清**：未能有效区分自我（Self）、其他AI（Other AI）和人类（Human）三者的身份。

## 改进目标

1. 实现真正的多轮对话能力
2. 让AI回复更加自然，减少格式化内容
3. 明确区分Self、Other AI和Human三种身份

## 现有结构利用

根据 existing structure，我们可以利用 `ai_group_members` 表中的 `member_type` 字段来区分身份：
- `member_type = 1` 表示AI成员
- `member_type = 0` 表示人类成员
- 通过 `member_id` 与当前AI的ID比较来确定是否为Self

## 具体实施方案

### 1. 多轮对话能力实现

#### 1.1 会话记忆机制
- 为每个群组维护一个长期对话历史
- 实现滑动窗口机制，保留最近N轮对话
- 为每个AI成员维护个性化记忆（只记住与自己的交互）

#### 1.2 上下文理解增强
- 引入对话状态追踪（如话题延续、情绪变化等）
- 实现指代消解（如"他刚才说的"指的是谁）
- 加强对对话历史的引用和回应

### 2. 自然化回复改进

#### 2.1 提示词优化
- 在提示词中明确要求使用自然、口语化的表达
- 减少模板化回复的倾向
- 鼓励使用日常对话中的连接词和语气词

#### 2.2 回复长度控制
- 限制回复长度，鼓励简洁明了的表达
- 避免一次性回答多个问题，采用逐步回应的方式

### 3. 三方身份区分（基于现有字段）

#### 3.1 消息分类标识（无需新增字段）
- 利用 `ai_group_members.member_type` 字段区分AI和人类
- 通过比较 `member_id` 与当前AI的ID区分Self和Other AI
- 在上下文中明确标注不同身份的发言

#### 3.2 角色感知提示
- 为每个AI提供明确的角色定位提示
- 在提示词中强调与其他AI和人类的区别
- 定义不同的回应策略针对不同身份的发言者

## 技术实现细节

### 1. 上下文构建优化（利用现有字段）

```python
def build_enhanced_context(
    self,
    target_member_id: int,
    group_id: int,
    message_limit: int = 20
) -> dict:
    """
    构建增强的对话上下文，区分Self/Other AI/Human（基于现有字段）
    """
    messages = self.get_recent_messages(group_id, message_limit)
    
    # 从数据库获取群组成员信息
    group_members = self.db.query(AiGroupMember).filter(
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
        "current_context": self.extract_current_context(messages)
    }
```

### 2. 提示词模板重构

```python
def create_role_aware_prompt(
    self,
    ai_member: AiGroupMember,
    context: dict
) -> str:
    """
    创建具有角色意识的提示词（基于现有字段）
    """
    return f"""
你是{ai_member.ai_nickname}，一个人格化AI助手。

【身份认知】
- 你的性格：{ai_member.personality}
- 你的立场：{ai_member.initial_stance}
- 你的说话风格：{ai_member.speaking_style or "自然随意"}

【对话伙伴识别】
- 人类参与者：他们有情感、偏好和主观意见，回应时要有温度
- 其他AI：它们有自己的角色设定和立场，可进行智识交流
- 你自己：保持一致的性格和立场

【历史回顾】
人类最近说了：
{self.format_messages(context['human_interactions'])}

其他AI最近说了：
{self.format_messages(context['other_ai_interactions'])}

你之前说过：
{self.format_messages(context['self_history'])}

【当前话题】
{context['current_context']}

【回应要求】
1. 使用自然、口语化的表达
2. 回应要简洁，通常不超过150字
3. 针对发言者身份调整回应风格
4. 保持你的角色一致性
5. 避免过度格式化，像真人聊天一样自然
"""
```

### 3. 消息处理流程改进

```python
async def generate_response(
    self,
    member_id: int,
    group_id: int,
    trigger_message: Optional[str] = None
) -> str:
    """生成AI响应"""
    
    # 1. 获取增强的上下文（基于现有字段）
    enhanced_context = self.build_enhanced_context(member_id, group_id)
    
    # 2. 构建角色感知提示词
    ai_member = self.get_ai_member(member_id)
    prompt = self.create_role_aware_prompt(ai_member, enhanced_context)
    
    # 3. 调用AI模型
    response = await self.ai_model_service.generate(
        model_name=ai_member.ai_model,
        prompt=prompt,
        max_tokens=300,  # 控制回复长度
        temperature=0.8  # 增加一些随机性使回复更自然
    )
    
    # 4. 后处理：去除过度格式化内容
    processed_response = self.post_process_response(response)
    
    return processed_response
```

## 实施步骤

### 第一阶段：基础架构改造
1. 修改上下文构建逻辑以利用现有字段
2. 实现消息分类功能（Self/Other AI/Human）
3. 实现基础的上下文分类功能

### 第二阶段：提示词优化
1. 重构提示词模板
2. 实现角色感知的上下文构建
3. 添加自然化后处理功能

### 第三阶段：高级功能
1. 实现对话状态追踪
2. 添加指代消解功能
3. 优化多轮对话连贯性

### 第四阶段：测试与优化
1. 进行多轮对话测试
2. 收集反馈并调整参数
3. 优化性能和稳定性

## 预期效果

实施以上改进后，AI群聊系统将具备：

1. **真正的多轮对话能力**：AI能够理解对话历史，进行连贯的交流
2. **自然的对话风格**：减少格式化内容，更像真实的人类对话
3. **清晰的身份区分**：AI能够识别并适当回应不同身份的参与者（基于现有字段）
4. **更好的用户体验**：整体对话体验更加流畅和自然