# AI群聊功能API文档

## 概述

本文档详细描述了AI群聊功能的API接口，该功能专注于AI角色差异化，使多个AI在同一群聊中表现出不同的角色特征。群组创建、成员添加和消息发送等基础功能已在其他API中实现，本API专注于AI特有的响应触发和角色管理功能。

## API基础信息

- **基础URL**: `/api/ai-group-chat`
- **协议**: HTTPS
- **内容类型**: `application/json`
- **认证**: JWT Token (在Header中使用 `Authorization: Bearer <token>`)

## 通用响应格式

所有API响应都遵循以下格式：

```json
{
  "success": true,
  "message": "操作成功的描述信息",
  "data": {
    // 具体的数据内容
  }
}
```

错误响应格式：

```json
{
  "success": false,
  "message": "错误描述信息",
  "data": null
}
```

## API端点详情

### 1. 触发AI响应

**端点**: `POST /api/ai-group-chat/ai/respond`

**描述**: 触发指定AI成员生成响应，这是AI群聊的核心功能

**请求参数**:
```json
{
  "group_id": 1,
  "member_id": 5,
  "trigger_message": "请发表你的看法",
  "force_trigger": false
}
```

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| group_id | integer | 是 | 群聊ID |
| member_id | integer | 是 | AI成员ID |
| trigger_message | string | 否 | 触发消息，如果提供将直接影响AI响应 |
| force_trigger | boolean | 否 | 是否强制触发，跳过相关性检测，默认false |

**请求示例**:
```bash
curl -X POST "https://your-domain.com/api/ai-group-chat/ai/respond" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{
    "group_id": 1,
    "member_id": 5,
    "trigger_message": "请发表你的看法",
    "force_trigger": false
  }'
```

**响应示例** (成功):
```json
{
  "success": true,
  "message": "AI响应生成成功",
  "data": {
    "message_id": 101,
    "content": "从我的角度来看，科技创新是推动社会进步的重要动力...",
    "created_at": "2023-10-01T10:05:00"
  }
}
```

**响应示例** (AI认为无需回应):
```json
{
  "success": false,
  "message": "AI认为当前不需要回应",
  "data": {
    "reasons": [
      {
        "message": "今天天气真好",
        "sender": "张三",
        "relevance_type": "not_relevant",
        "score": 0.0
      }
    ]
  }
}
```

**错误码**:
- `400`: AI成员不属于指定群组
- `404`: AI成员不存在
- `500`: AI响应生成失败

---

### 2. 获取群聊详情

**端点**: `GET /api/ai-group-chat/group/{group_id}`

**描述**: 获取指定群聊的详细信息，包括成员和消息，特别突出AI成员的人格和立场信息

**路径参数**:
- `group_id`: 群聊ID

**请求示例**:
```bash
curl -X GET "https://your-domain.com/api/ai-group-chat/group/1" \
  -H "Authorization: Bearer your-jwt-token"
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "AI辩论群",
    "created_at": "2023-10-01T09:00:00",
    "members": [
      {
        "id": 5,
        "nickname": "辩论专家",
        "member_type": 1,
        "personality": "逻辑严谨，善于反驳",
        "initial_stance": "支持科技创新"
      }
    ],
    "messages": [
      {
        "id": 100,
        "sender_nickname": "辩论专家",
        "content": "大家好，今天我们讨论科技发展。",
        "message_type": "text",
        "created_at": "2023-10-01T10:00:00"
      }
    ]
  }
}
```

**错误码**:
- `404`: 群组不存在
- `500`: 服务器内部错误

---

### 3. 获取群聊消息

**端点**: `GET /api/ai-group-chat/messages/{group_id}`

**描述**: 获取指定群聊的消息列表

**路径参数**:
- `group_id`: 群聊ID

**查询参数**:
- `skip`: 跳过的消息数，默认0
- `limit`: 返回的消息数，默认50，最大100

**请求示例**:
```bash
curl -X GET "https://your-domain.com/api/ai-group-chat/messages/1?skip=0&limit=20" \
  -H "Authorization: Bearer your-jwt-token"
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": 100,
        "member_id": 5,
        "sender_nickname": "辩论专家",
        "content": "大家好，今天我们讨论科技发展。",
        "message_type": "text",
        "created_at": "2023-10-01T10:00:00"
      }
    ],
    "pagination": {
      "skip": 0,
      "limit": 20,
      "total": 1
    }
  }
}
```

**错误码**:
- `404`: 群组不存在
- `500`: 服务器内部错误

---

### 4. 获取AI成员特征

**端点**: `GET /api/ai-group-chat/ai-member/{member_id}/characteristics`

**描述**: 获取AI成员的特征信息，用于前端显示AI的人格和立场信息

**路径参数**:
- `member_id`: AI成员ID

**请求示例**:
```bash
curl -X GET "https://your-domain.com/api/ai-group-chat/ai-member/5/characteristics" \
  -H "Authorization: Bearer your-jwt-token"
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 5,
    "nickname": "辩论专家",
    "personality": "逻辑严谨，善于反驳",
    "initial_stance": "支持科技创新",
    "ai_model": "gpt-4"
  }
}
```

**错误码**:
- `404`: AI成员不存在
- `500`: 服务器内部错误

## AI角色差异化机制

### 人格特征 (Personality)
AI的人格特征会影响其回应的方式和风格。例如：
- "逻辑严谨，善于反驳" → AI会以逻辑性强、喜欢挑战观点的方式回应
- "温和友善，善于倾听" → AI会以温和、支持性的语气回应
- "创新思维，天马行空" → AI会提出新颖、有创意的观点

### 初始立场 (Initial Stance)
AI的初始立场决定了其在特定话题上的基本观点。系统会确保AI在对话中保持其立场的一致性。

### 相关性检测
系统会检测消息与特定AI的相关性，只有在以下情况下才会触发AI回应：
1. 直接@提及AI
2. 消息内容与AI的立场或人格相关
3. 消息是对AI之前发言的回复
4. 消息涉及AI专业领域的话题

## 错误处理

| HTTP状态码 | 描述 | 可能原因 |
|------------|------|----------|
| 200 | 请求成功 | 操作正常完成 |
| 400 | 请求参数错误 | 提供的参数无效或缺失 |
| 401 | 未授权 | JWT Token缺失或无效 |
| 404 | 资源不存在 | 指定的群组或成员不存在 |
| 500 | 服务器内部错误 | 服务器遇到意外情况 |

## 速率限制

为防止单个用户滥用API，系统对以下端点实施速率限制：
- `/ai/respond`: 每分钟最多10次请求

## 部署说明

1. 确保数据库中有`ai_chat_groups`、`ai_group_members`、`ai_messages`和`ai_models`表
2. 在环境变量中配置AI模型的API密钥和端点
3. 确保后端服务能够访问AI模型API
4. 配置JWT认证中间件

## 开发指南

### 添加新的AI模型支持
1. 在`ai_models`表中添加新模型记录
2. 在`AiModelService`中添加相应的API调用方法
3. 更新模型验证逻辑

### 扩展人格特征检测
1. 修改`MessageRelevanceDetector`中的相关性算法
2. 添加新的检测维度
3. 调整相关性阈值

### 自定义响应验证
1. 扩展`RoleConsistencyMiddleware`类
2. 添加新的验证规则
3. 调整一致性评分算法