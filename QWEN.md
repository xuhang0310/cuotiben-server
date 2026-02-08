# 错题本系统 (Cuoti Ben) - 后端项目上下文

## 项目概述

这是一个基于 FastAPI 的智能化学习辅助平台后端系统，名为“错题本系统”（cuotiben-server）。该项目提供了一套完整的后端API服务，支持用户注册登录、练习管理、历史人物问答、AI对话等功能，旨在帮助学生高效管理和复习错题，提升学习效率。

## 技术栈

- **Web框架**: FastAPI - 提供高性能的API服务
- **数据库**: MySQL - 存储用户数据和练习记录
- **ORM**: SQLAlchemy - 数据库操作抽象层
- **认证机制**: JWT - 安全的用户身份验证
- **异步支持**: asyncio - 高效处理并发请求
- **图像处理**: Pillow - 处理上传的图片文件
- **安全与加密**: python-jose, passlib - 密码哈希和JWT处理

## 项目结构

```
cuotiben-server/
├── app/
│   ├── __init__.py
│   ├── main.py                 # 应用入口
│   ├── api/                    # API路由模块
│   │   ├── auth.py             # 认证相关接口
│   │   ├── historical_figures.py # 历史人物接口
│   │   ├── conversations.py    # 对话接口
│   │   ├── upload.py           # 文件上传接口
│   │   ├── qwen_ai.py          # 通义千问AI接口
│   │   ├── ai_chat.py          # AI聊天接口
│   │   └── ...
│   ├── models/                 # 数据模型定义
│   │   ├── user.py             # 用户模型
│   │   ├── subject.py          # 学科模型
│   │   ├── question.py         # 问题模型
│   │   ├── practice_record.py  # 练习记录模型
│   │   └── ...
│   ├── schemas/                # Pydantic数据验证模型
│   ├── services/               # 业务逻辑服务
│   ├── utils/                  # 工具函数
│   ├── core/                   # 核心配置
│   │   └── config.py           # 配置管理
│   └── database/
│       └── session.py          # 数据库会话管理
├── init_db.py                  # 数据库初始化脚本
├── run.py                      # 启动脚本
├── start.sh                    # 启动Shell脚本
├── requirements.txt            # 依赖列表
├── .env.example                # 环境变量示例
├── README.md                   # 项目说明
└── USAGE.md                    # 使用说明
```

## 核心功能

### 1. 用户管理
- **用户注册**: 新用户可以通过注册接口创建账户
- **用户登录**: 通过用户名和密码进行身份验证，获取JWT访问令牌
- **个人信息管理**: 查看和更新个人资料

### 2. 练习系统
- **开始练习**: 用户可以选择学科开始练习模式
- **提交答案**: 练习过程中可提交答案，系统会记录练习进度
- **练习统计**: 查看练习历史和统计数据，了解学习进展

### 3. 历史人物问答
- **人物查询**: 通过API查询历史人物相关信息
- **智能问答**: 与历史人物进行互动问答，加深对历史知识的理解

### 4. AI对话助手
- **智能聊天**: 与AI助手进行自然语言对话
- **学习辅助**: 获取学习建议和解题思路

### 5. 内容管理
- **文件上传**: 支持图片等多媒体文件上传功能
- **内容生成**: 通过提示词生成相关内容

## 环境配置

### 环境要求
- Python 3.8+
- MySQL数据库
- pip包管理器

### 配置文件
项目使用 `.env` 文件存储敏感配置信息，包括：
- 数据库连接信息 (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
- JWT密钥 (SECRET_KEY)
- 阿里云API密钥 (ALIBABA_CLOUD_API_KEY)
- 服务器配置 (HOST, PORT, SERVER_DOMAIN)

### 数据库初始化
运行 `init_db.py` 脚本会自动创建以下表：
- users: 用户表
- subjects: 学科表
- questions: 问题表
- question_options: 问题选项表
- tags: 标签表
- question_tags: 问题标签关联表
- practice_records: 练习记录表
- user_settings: 用户设置表

## 启动方式

### 开发模式
```bash
# 1. 创建虚拟环境并安装依赖
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接信息

# 3. 初始化数据库
python init_db.py

# 4. 启动服务器
python run.py
```

### 使用启动脚本（推荐）
```bash
./start.sh
```

### 访问API文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API端点

### 认证相关
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

### 练习系统
- `POST /api/practice/start` - 开始练习
- `POST /api/practice/submit` - 提交答案
- `GET /api/practice/stats` - 获取练习统计

### 历史人物
- `GET /api/historical-figures` - 获取历史人物列表
- `GET /api/historical-figures/{id}` - 获取特定历史人物信息

### AI对话
- `POST /api/chat` - 与AI助手对话

### 文件上传
- `POST /api/upload/image` - 上传图片文件

## 开发约定

### 代码规范
- 遵循PEP 8代码规范
- 使用类型提示
- 编写清晰的文档字符串
- 添加适当的错误处理

### 异常处理
项目实现了全局异常处理器，统一返回格式为：
```json
{
  "status": "error",
  "code": 401,
  "detail": "Unauthorized"
}
```

### 日志记录
使用Python标准logging模块记录应用运行状态，便于调试和监控。

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

## 测试

项目包含API测试文件：
- `test_complete_api.py` - 完整API测试
- `test_qwen_api.py` - 通义千问API测试

运行测试：
```bash
python test_complete_api.py
python test_qwen_api.py
```