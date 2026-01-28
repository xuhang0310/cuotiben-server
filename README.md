# 错题本系统 - 后端API

## 项目概述

错题本系统是一个智能化的学习辅助平台，帮助学生高效管理和复习错题，提升学习效率。本项目提供了一套完整的后端API服务，支持用户注册登录、练习管理、历史人物问答、AI对话等功能。

## 核心功能

### 1. 用户管理
- **用户注册**：新用户可以通过注册接口创建账户
- **用户登录**：通过用户名和密码进行身份验证，获取访问令牌
- **个人信息管理**：查看和更新个人资料

### 2. 练习系统
- **开始练习**：用户可以选择学科开始练习模式
- **提交答案**：练习过程中可提交答案，系统会记录练习进度
- **练习统计**：查看练习历史和统计数据，了解学习进展

### 3. 历史人物问答
- **人物查询**：通过API查询历史人物相关信息
- **智能问答**：与历史人物进行互动问答，加深对历史知识的理解

### 4. AI对话助手
- **智能聊天**：与AI助手进行自然语言对话
- **学习辅助**：获取学习建议和解题思路

### 5. 内容管理
- **文件上传**：支持图片等多媒体文件上传功能
- **内容生成**：通过提示词生成相关内容

## 技术架构

- **Web框架**: FastAPI - 提供高性能的API服务
- **数据库**: MySQL - 存储用户数据和练习记录
- **认证机制**: JWT - 安全的用户身份验证
- **异步支持**: asyncio - 高效处理并发请求

## 快速开始

### 环境要求
- Python 3.8+
- MySQL数据库
- pip包管理器

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd cuotiben-server
   ```

2. **创建虚拟环境并安装依赖**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # Windows: venv\Scripts\activate
   
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，配置数据库连接信息
   ```

4. **初始化数据库**
   ```bash
   python init_db.py
   ```

5. **启动服务器**
   ```bash
   python run.py
   ```

6. **访问API文档**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API使用指南

### 认证流程
1. **注册用户**: `POST /api/auth/register`
2. **登录获取令牌**: `POST /api/auth/login`
3. **使用令牌访问受保护资源**: 在请求头中添加 `Authorization: Bearer <token>`

### 主要功能接口

#### 用户管理
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

#### 练习系统
- `POST /api/practice/start` - 开始练习
- `POST /api/practice/submit` - 提交答案
- `GET /api/practice/stats` - 获取练习统计

#### 历史人物问答
- `GET /api/historical-figures` - 获取历史人物列表
- `GET /api/historical-figures/{id}` - 获取特定历史人物信息

#### AI对话
- `POST /api/chat` - 与AI助手对话

#### 文件上传
- `POST /api/upload/image` - 上传图片文件

## 部署说明

### 生产环境部署
1. 使用Gunicorn或Uvicorn作为ASGI服务器
2. 配置Nginx作为反向代理
3. 设置SSL证书以启用HTTPS
4. 配置数据库连接池和缓存机制

### Docker部署（可选）
```dockerfile
FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 项目结构

```
cuotiben-server/
├── app/
│   ├── main.py                 # 应用入口
│   ├── database/               # 数据库配置
│   ├── models/                 # 数据模型
│   ├── schemas/                # 数据验证模型
│   ├── api/                    # API路由
│   │   ├── auth.py             # 认证相关接口
│   │   ├── users.py            # 用户管理接口
│   │   ├── practice.py         # 练习系统接口
│   │   ├── historical_figures.py # 历史人物接口
│   │   ├── conversations.py    # 对话接口
│   │   └── upload.py           # 文件上传接口
│   ├── core/                   # 核心配置
│   └── utils/                  # 工具函数
├── init_db.py                  # 数据库初始化脚本
├── run.py                      # 启动脚本
├── requirements.txt            # 依赖列表
└── README.md                   # 项目说明
```

## 贡献指南

我们欢迎社区贡献！如果您想为项目做出贡献：

1. Fork项目仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 支持

如果您遇到任何问题或有任何建议，请通过以下方式联系我们：
- 提交Issue
- 发送邮件至 [support@example.com](mailto:support@example.com)