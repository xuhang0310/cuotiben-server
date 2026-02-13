#!/bin/bash

# 图片压缩工具 - Docker 一键启动脚本（Mac/Linux）

set -e

echo "=========================================="
echo "  图片压缩工具 - Docker 一键启动"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[错误] 未检测到 Docker！${NC}"
    echo ""
    echo "请先安装 Docker："
    echo "  Mac: https://docs.docker.com/desktop/install/mac-install/"
    echo "  Linux: https://docs.docker.com/engine/install/"
    exit 1
fi

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}[错误] 未检测到 Docker Compose！${NC}"
    echo "请更新到最新版 Docker"
    exit 1
fi

echo -e "${GREEN}[1/4] 正在检查 Docker 服务...${NC}"
if ! docker info &> /dev/null; then
    echo -e "${RED}[错误] Docker 服务未启动！${NC}"
    echo "请启动 Docker Desktop 或运行: sudo systemctl start docker"
    exit 1
fi
echo -e "${GREEN}[OK] Docker 服务正常${NC}"
echo ""

echo -e "${GREEN}[2/4] 正在构建 Docker 镜像...${NC}"
echo "首次构建可能需要 5-10 分钟，请耐心等待..."
if ! docker-compose build --no-cache; then
    echo -e "${RED}[错误] 镜像构建失败！${NC}"
    exit 1
fi
echo -e "${GREEN}[OK] 镜像构建完成${NC}"
echo ""

echo -e "${GREEN}[3/4] 正在启动服务...${NC}"
if ! docker-compose up -d; then
    echo -e "${RED}[错误] 服务启动失败！${NC}"
    exit 1
fi
echo -e "${GREEN}[OK] 服务已启动${NC}"
echo ""

echo -e "${GREEN}[4/4] 等待服务就绪...${NC}"
sleep 3

echo ""
echo "=========================================="
echo -e "${GREEN}  启动成功！${NC}"
echo "=========================================="
echo ""
echo "访问地址：http://localhost:8000"
echo ""

# 尝试打开浏览器（Mac）
if command -v open &> /dev/null; then
    echo "正在打开浏览器..."
    open http://localhost:8000
fi

# 尝试打开浏览器（Linux）
if command -v xdg-open &> /dev/null; then
    echo "正在打开浏览器..."
    xdg-open http://localhost:8000 &
fi

echo ""
echo "常用命令："
echo "  查看日志：docker-compose logs -f"
echo "  停止服务：docker-compose down"
echo "  重启服务：docker-compose restart"
echo ""
