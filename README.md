# Python后端实现规划

## 技术栈选择

- **Web框架**: FastAPI - 现代、快速（高性能）的Web框架，基于Python类型提示
- **数据库**: MySQL - 与原有后端保持一致
- **ORM**: SQLAlchemy - Python SQL工具包和ORM
- **异步支持**: async/await - 提供高性能异步处理
- **依赖管理**: pipenv 或 poetry
- **环境配置**: python-dotenv
- **文件上传**: python-multipart
- **JWT认证**: python-jose[cryptography]
- **OCR识别**: PaddleOCR - 飞桨OCR引擎

## 项目结构

```
backend-py/
├── app/
│   ├── __init__.py
│   ├── main.py                 # 应用入口
│   ├── database/               # 数据库配置
│   │   ├── __init__.py
│   │   └── session.py          # 数据库会话配置
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── subject.py
│   │   ├── question_type.py
│   │   ├── question.py
│   │   ├── question_option.py
│   │   ├── tag.py
│   │   ├── question_tag.py
│   │   ├── practice_record.py
│   │   ├── answer_template.py
│   │   ├── review_schedule.py
│   │   └── user_settings.py
│   ├── schemas/                # Pydantic模型（请求/响应）
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── subject.py
│   │   ├── question_type.py
│   │   ├── question.py
│   │   ├── tag.py
│   │   ├── practice_record.py
│   │   ├── statistics.py
│   │   └── settings.py
│   ├── api/                    # API路由
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── subjects.py
│   │   ├── question_types.py
│   │   ├── tags.py
│   │   ├── questions.py
│   │   ├── practice.py
│   │   ├── statistics.py
│   │   ├── settings.py
│   │   └── ocr.py
│   ├── core/                   # 核心配置和安全
│   │   ├── __init__.py
│   │   ├── config.py           # 配置管理
│   │   ├── security.py         # 安全相关（JWT、密码哈希等）
│   │   └── dependencies.py     # 依赖注入
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       └── ocr.py              # OCR相关工具
├── tests/                      # 测试文件
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_questions.py
│   └── ...
├── requirements.txt            # 依赖列表
├── .env                       # 环境变量配置
├── .env.example               # 环境变量示例
└── README.md                  # 项目说明
```

## 数据库模型映射

与原有Node.js后端保持一致的数据库表结构：

1. users - 用户表
2. subjects - 学科表
3. question_types - 题型表
4. questions - 题目表
5. question_options - 题目选项表
6. tags - 标签表
7. question_tags - 题目标签关联表
8. practice_records - 练习记录表
9. answer_templates - 答案模板表
10. review_schedules - 复习计划表
11. user_settings - 用户设置表

## API端点映射

### 认证相关接口
- POST /api/auth/register - 用户注册
- POST /api/auth/login - 用户登录
- GET /api/auth/me - 获取当前用户信息

### 题目管理接口
- GET /api/questions - 获取题目列表
- GET /api/questions/{id} - 获取题目详情
- POST /api/questions - 创建题目
- PUT /api/questions/{id} - 更新题目
- DELETE /api/questions/{id} - 删除题目
- POST /api/questions/{id}/toggle-favorite - 切换收藏状态

### 练习接口
- POST /api/practice/start - 开始练习
- POST /api/practice/submit - 提交答案
- GET /api/practice/stats - 获取练习统计数据

### 统计接口
- GET /api/statistics - 获取统计数据

### 设置接口
- GET /api/settings - 获取用户设置
- PUT /api/settings - 更新用户设置

### 拍照录题接口
- POST /api/ocr/recognize - OCR识别（上传图片文件）
- POST /api/ocr/recognize-from-url - OCR识别（网络图片URL）
- POST /api/ocr/save-question - 保存OCR识别的题目

### 管理接口
- GET /api/tags - 获取所有标签
- GET /api/tags/{id} - 获取标签详情
- POST /api/tags - 创建标签
- GET /api/subjects - 获取所有学科
- GET /api/subjects/{id} - 获取学科详情
- POST /api/subjects - 创建学科
- GET /api/question-types - 获取所有题型
- GET /api/question-types/{id} - 获取题型详情
- POST /api/question-types - 创建题型
- GET /api/users - 获取所有用户
- GET /api/users/{id} - 获取用户详情
- POST /api/users - 创建用户

## 开发计划

### 第一阶段：基础架构搭建
1. 创建项目结构
2. 配置数据库连接
3. 实现核心配置和安全模块
4. 创建基础数据模型

### 第二阶段：认证系统实现
1. 实现用户注册、登录功能
2. 实现JWT令牌生成和验证
3. 实现密码哈希处理

### 第三阶段：核心功能实现
1. 实现题目管理API
2. 实现练习系统API
3. 实现统计系统API
4. 实现设置管理API

### 第四阶段：扩展功能实现
1. 实现OCR识别功能（使用飞桨OCR）
2. 实现标签、学科、题型管理API
3. 实现用户管理API

### 第五阶段：测试和优化
1. 编写单元测试
2. 性能优化
3. 安全性检查
4. 文档完善

## 运行项目

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 配置环境变量：
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，设置正确的数据库连接信息和其他配置
   ```

3. 运行项目：
   ```bash
   python run.py
   ```

4. 访问API文档：
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## OCR功能说明

本项目集成了飞桨OCR引擎，用于识别图片中的文字内容：

1. 使用PaddleOCR进行文字识别
2. 支持中英文混合识别
3. 自动下载预训练模型
4. 识别失败时自动回退到模拟数据

## 部署说明

1. 生产环境建议使用Gunicorn或Uvicorn作为WSGI服务器
2. 建议使用Nginx作为反向代理
3. 数据库连接池配置优化
4. 日志记录和监控配置