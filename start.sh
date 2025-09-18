#!/bin/bash

# 后端Python项目启动脚本

echo "🚀 启动错题本系统Python后端..."

# 检查Python环境
if ! command -v python3 &> /dev/null
then
    echo "❌ 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查pip
if ! command -v pip &> /dev/null
then
    echo "❌ 未找到pip，请先安装pip"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "🔧 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "🔧 安装项目依赖..."
pip install -r requirements.txt

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "🔧 创建环境配置文件..."
    cp .env.example .env
    echo "⚠️  请编辑.env文件，配置数据库连接信息和其他设置"
fi

# 启动服务器
echo "🚀 启动服务器..."
echo "📖 API文档地址:"
echo "   - Swagger UI: http://localhost:8000/docs"
echo "   - ReDoc: http://localhost:8000/redoc"
echo "🔧 按Ctrl+C停止服务器"

python run.py