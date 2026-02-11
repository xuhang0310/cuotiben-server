#!/bin/bash
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
# 后端Python项目启动脚本 - 后台运行版本（清爽版）

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

# 创建日志目录
LOG_DIR="logs"
if [ ! -d "$LOG_DIR" ]; then
    echo "📁 创建日志目录: $LOG_DIR"
    mkdir -p "$LOG_DIR"
fi

# 设置日志文件路径（清爽格式：无日期）
LOG_FILE="$LOG_DIR/app.log"
PID_FILE="server.pid"

echo "📝 日志文件: $LOG_FILE"

# 检查是否已运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  服务已在运行 (PID: $PID)"
        echo "🔧 重启服务..."
        kill $PID
        sleep 2
    else
        echo "🗑️  清理旧的PID文件"
        rm "$PID_FILE"
    fi
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "🔧 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖（使用清爽的日志文件名）
echo "🔧 安装项目依赖..."
pip install -r requirements.txt > "$LOG_DIR/install.log" 2>&1

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "🔧 创建环境配置文件..."
    cp .env.example .env
    echo "⚠️  请编辑.env文件，配置数据库连接信息和其他设置"
fi

# 启动服务器（后台运行）
echo "🚀 启动服务器（后台运行）..."

# 运行服务并保存PID
nohup python run.py >> "$LOG_FILE" 2>&1 &
SERVER_PID=$!

# 保存PID到文件
echo $SERVER_PID > "$PID_FILE"
echo "✅ 服务已启动 (PID: $SERVER_PID)"

# 显示启动信息
echo ""
echo "=================================================="
echo "错题本系统启动成功！"
echo "=================================================="
echo "📊 服务信息:"
echo "   🔹 PID: $SERVER_PID"
echo "   🔹 日志: $LOG_FILE"
echo "   🔹 PID文件: $PID_FILE"
echo ""
echo "🌐 访问地址:"
echo "   🔹 本地: http://localhost:8000"
echo "   🔹 文档: http://localhost:8000/docs"
echo ""
echo "🔧 管理命令:"
echo "   🔸 查看日志: tail -f $LOG_FILE"
echo "   🔸 停止服务: ./stop_server.sh"
echo "   🔸 重启服务: ./restart_server.sh"
echo "=================================================="

# 显示最近日志
echo ""
echo "📋 最近日志:"
echo "----------------------------------------"
tail -20 "$LOG_FILE" 2>/dev/null || echo "等待日志生成..."
echo "----------------------------------------"
echo ""
echo "🔍 实时查看日志: tail -f $LOG_FILE"