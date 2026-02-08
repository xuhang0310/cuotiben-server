# AI群聊功能设计方案

## 概述

本文档详细描述了AI群聊功能的设计方案，包括数据库表结构分析、API设计、上下文存储机制等内容。该功能允许用户在群聊环境中与多个AI角色进行交互，每个AI角色具有独特的个性和立场。

## 现有表结构分析

根据现有代码，AI群聊功能涉及以下三个核心表：

### 1. ai_chat_groups 表
- 存储群聊基本信息
- 字段：id, name, created_at, updated_at, status, user_id

### 2. ai_group_members 表
- 存储群聊中的成员信息
- 区分人类成员和AI成员
- 字段：id, group_id, ai_model, ai_nickname, personality, initial_stance, created_at, user_id, member_type

### 3. ai_messages 表
- 存储群聊中的消息记录
- 字段：id, group_id, member_id, content, message_type, created_at

### 4. ai_models 表
- 存储可用的AI模型信息
- 字段：id, model_name, description, api_key, api_secret, endpoint, is_active, created_at, updated_at

## API设计

### 1. 群组管理API

#### 创建群聊
- **端点**: `POST /api/ai-chat/group/create`
- **请求体**:
  ```json
  {
    "name": "群聊名称",
    "user_id": "创建人ID"
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "data": {
      "id": "群聊ID",
      "name": "群聊名称",
      "created_at": "创建时间"
    }
  }
  ```

#### 获取群聊详情
- **端点**: `GET /api/ai-chat/group/{group_id}`
- **响应**:
  ```json
  {
    "success": true,
    "data": {
      "id": "群聊ID",
      "name": "群聊名称",
      "members": [
        {
          "id": "成员ID",
          "nickname": "昵称",
          "member_type": "成员类型(0-人类, 1-AI)",
          "personality": "个性描述(仅AI)"
        }
      ],
      "messages": [
        {
          "id": "消息ID",
          "member_id": "发送者ID",
          "content": "消息内容",
          "created_at": "发送时间"
        }
      ]
    }
  }
  ```

#### 删除群聊
- **端点**: `DELETE /api/ai-chat/group/{group_id}`
- **响应**:
  ```json
  {
    "success": true,
    "message": "群聊删除成功"
  }
  ```

### 2. 成员管理API

#### 添加成员
- **端点**: `POST /api/ai-chat/member/add`
- **请求体**:
  ```json
  {
    "group_id": "群聊ID",
    "member_type": "成员类型(0-人类, 1-AI)",
    "ai_model": "AI模型名称(仅AI成员)",
    "ai_nickname": "AI昵称",
    "personality": "个性描述(仅AI成员)",
    "initial_stance": "初始立场(仅AI成员)",
    "user_id": "用户ID(仅人类成员)"
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "data": {
      "id": "成员ID",
      "group_id": "群聊ID",
      "member_type": "成员类型"
    }
  }
  ```

#### 移除成员
- **端点**: `DELETE /api/ai-chat/member/{member_id}`
- **响应**:
  ```json
  {
    "success": true,
    "message": "成员移除成功"
  }
  ```

### 3. 消息和AI交互API

#### 发送消息
- **端点**: `POST /api/ai-chat/message/send`
- **请求体**:
  ```json
  {
    "group_id": "群聊ID",
    "member_id": "发送者成员ID",
    "content": "消息内容",
    "message_type": "消息类型(text, image, file)"
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "data": {
      "id": "消息ID",
      "group_id": "群聊ID",
      "member_id": "发送者ID",
      "content": "消息内容",
      "created_at": "发送时间"
    }
  }
  ```

#### 触发AI回复
- **端点**: `POST /api/ai-chat/ai/respond/{member_id}`
- **请求体**:
  ```json
  {
    "group_id": "群聊ID",
    "trigger_message": "触发消息内容(可选)"
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "data": {
      "message_id": "新消息ID",
      "content": "AI回复内容"
    }
  }
  ```

### 4. 消息检索API

#### 获取群聊消息
- **端点**: `GET /api/ai-chat/messages/{group_id}?page=1&size=20`
- **响应**:
  ```json
  {
    "success": true,
    "data": {
      "messages": [
        {
          "id": "消息ID",
          "member_id": "发送者ID",
          "member_nickname": "发送者昵称",
          "content": "消息内容",
          "message_type": "消息类型",
          "created_at": "发送时间"
        }
      ],
      "pagination": {
        "page": 1,
        "size": 20,
        "total": 100
      }
    }
  }
  ```

## 上下文存储机制

### 1. 数据库上下文存储

利用现有的 `ai_messages` 表作为主要的上下文存储机制：

- 每条消息按时间顺序存储，确保可以重建完整的对话历史
- 通过 `group_id` 和 `created_at` 索引快速检索特定群组的消息
- 实现滑动窗口机制，每次AI回复时获取最近的N条消息作为上下文

### 2. 上下文检索策略

#### 时间窗口法
- 检索过去X分钟内的所有消息
- 适用于实时性要求高的场景

#### 消息数量窗口法
- 检索最新的N条消息
- 适用于控制上下文长度的场景

#### 混合策略
- 结合时间和消息数量限制
- 默认获取最近20条消息或过去2小时内所有消息（以较小者为准）

### 3. 内存优化策略

#### Redis缓存
- 使用Redis缓存活跃群聊的上下文
- 设置合理的过期时间（如30分钟无活动后清除）
- 减少数据库查询压力

#### 上下文摘要
- 对于长对话，定期生成对话摘要
- 保留关键信息，减少上下文长度

### 4. 上下文增强

#### 人格信息注入
- 在调用AI模型时，将AI成员的 `personality` 和 `initial_stance` 信息作为系统提示注入
- 确保AI回复符合其预设的人格特征

#### 群组元数据
- 将群组名称和主题作为上下文的一部分
- 帮助AI理解对话背景

## 工作流程

### 1. 用户触发AI发言
1. 前端发送请求到 `/api/ai-chat/ai/respond/{member_id}`
2. 后端验证成员ID和群组权限
3. 从数据库检索最近的对话上下文
4. 结合AI成员的人格信息构造完整提示
5. 调用对应的AI模型API
6. 将AI回复保存到 `ai_messages` 表
7. 返回新消息给前端

### 2. 连续AI对话
1. 用户点击第一个AI头像，该AI发言
2. 用户点击第二个AI头像，第二个AI基于完整上下文发言
3. 每次AI发言都会更新数据库中的消息记录
4. 所有参与方都能看到完整的对话历史

## 性能考虑

### 1. 数据库优化
- 为 `ai_messages.group_id` 和 `ai_messages.created_at` 创建复合索引
- 定期归档旧消息以保持查询性能

### 2. API限流
- 对AI调用接口实施速率限制
- 防止滥用和过度消耗API配额

### 3. 缓存策略
- 缓存AI模型配置信息
- 缓存活跃群聊的基本信息

## 安全考虑

### 1. 权限验证
- 验证用户是否有权访问特定群聊
- 验证用户是否有权添加/删除成员

### 2. 内容审核
- 对AI生成的内容进行适当过滤
- 防止不当内容传播

### 3. API密钥管理
- 安全存储和使用AI模型的API密钥
- 实施密钥轮换策略

## 扩展性考虑

### 1. 多AI模型支持
- 通过 `ai_models` 表支持多种AI模型
- 可以灵活切换不同能力的AI模型

### 2. 插件化架构
- 设计可扩展的AI适配器接口
- 便于集成新的AI服务提供商

### 3. 消息类型扩展
- 当前支持文本、图片、文件
- 可扩展支持更多媒体类型