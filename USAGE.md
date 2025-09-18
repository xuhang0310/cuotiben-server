# 项目使用说明

## 快速开始

### 1. 环境准备

确保系统已安装以下软件：
- Python 3.8+
- MySQL数据库
- pip包管理器

### 2. 克隆项目

```bash
cd /path/to/your/workspace
```

### 3. 使用启动脚本（推荐）

```bash
cd backend-py
./start.sh
```

### 4. 手动安装和运行

#### 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或者在Windows上: venv\Scripts\activate
```

#### 安装依赖
```bash
pip install -r requirements.txt
```

#### 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接信息
```

#### 初始化数据库
```bash
python init_db.py
```

#### 运行服务器
```bash
python run.py
```

## 环境配置

### 数据库配置
在 `.env` 文件中配置以下参数：
```env
# 数据库配置
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=study_ok
DB_PORT=3306

# JWT配置
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 服务器配置
HOST=127.0.0.1
PORT=8000
```

### 数据库表结构
运行 `init_db.py` 脚本会自动创建以下表：
- users: 用户表
- subjects: 学科表
- question_types: 题型表
- questions: 题目表
- question_options: 题目选项表
- tags: 标签表
- question_tags: 题目标签关联表
- practice_records: 练习记录表
- user_settings: 用户设置表

## API使用

### 认证流程
1. 注册用户: `POST /api/auth/register`
2. 登录获取令牌: `POST /api/auth/login`
3. 在后续请求中添加认证头: `Authorization: Bearer <token>`

### 主要API端点

#### 认证相关
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

#### 题目管理
- `GET /api/questions/` - 获取题目列表
- `GET /api/questions/{id}` - 获取题目详情
- `POST /api/questions/` - 创建题目
- `PUT /api/questions/{id}` - 更新题目
- `DELETE /api/questions/{id}` - 删除题目
- `POST /api/questions/{id}/toggle-favorite` - 切换收藏状态

#### 练习系统
- `POST /api/practice/start` - 开始练习
- `POST /api/practice/submit` - 提交答案
- `GET /api/practice/stats` - 获取练习统计

#### 统计系统
- `GET /api/statistics/` - 获取统计数据

#### OCR功能
- `POST /api/ocr/recognize` - OCR识别
- `POST /api/ocr/save-question` - 保存识别结果

#### 设置管理
- `GET /api/settings/` - 获取用户设置
- `PUT /api/settings/` - 更新用户设置

## 测试

### 运行测试
```bash
python -m pytest tests/
```

### API测试
```bash
python test_api.py
```

## 部署

### 生产环境部署建议

1. 使用Gunicorn作为WSGI服务器：
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

2. 使用Docker容器化部署：
```dockerfile
FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "run.py"]
```

3. 使用Nginx作为反向代理

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查 `.env` 文件中的数据库配置
   - 确保MySQL服务正在运行
   - 验证数据库用户权限

2. **模块导入错误**
   - 确保在项目根目录运行脚本
   - 检查Python路径设置
   - 确认所有依赖已正确安装

3. **端口被占用**
   - 修改 `.env` 文件中的PORT配置
   - 或者终止占用端口的进程

### 日志查看
查看控制台输出获取详细的错误信息和调试信息。

## 开发指南

### 添加新的API端点
1. 在 `app/api/` 目录下创建新的路由文件
2. 在 `app/main.py` 中注册路由
3. 创建相应的Pydantic模型（如果需要）
4. 创建相应的数据库模型（如果需要）

### 添加新的数据库表
1. 在 `app/models/` 目录下创建新的模型文件
2. 在相关API中使用新模型
3. 运行 `init_db.py` 更新数据库结构

### 代码规范
- 遵循PEP 8代码规范
- 使用类型提示
- 编写清晰的文档字符串
- 添加适当的错误处理