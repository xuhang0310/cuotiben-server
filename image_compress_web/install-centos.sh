#!/bin/bash

# 图片压缩工具 - CentOS/RHEL 一键安装脚本
# 适用于 CentOS 7/8, Rocky Linux, AlmaLinux

set -e

echo "=========================================="
echo "  图片压缩工具 - CentOS 安装向导"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[错误] 请使用 root 权限运行此脚本${NC}"
    echo "使用方法: sudo bash install-centos.sh"
    exit 1
fi

# 检测系统版本
echo -e "${BLUE}[信息] 正在检测系统...${NC}"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
    echo -e "${GREEN}检测到系统: $OS $VER${NC}"
else
    echo -e "${RED}无法检测系统版本${NC}"
    exit 1
fi

# 配置国内镜像源
echo -e "${BLUE}[步骤 1/8] 配置国内镜像源...${NC}"
if [[ $OS == *"CentOS"* ]] || [[ $OS == *"Rocky"* ]] || [[ $OS == *"AlmaLinux"* ]]; then
    # 更换阿里云镜像
    if [ -f /etc/yum.repos.d/CentOS-Base.repo ]; then
        cp /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.bak
        curl -o /etc/yum.repos.d/CentOS-Base.repo https://mirrors.aliyun.com/repo/Centos-${VER%%.*}.repo
        yum clean all
        yum makecache
        echo -e "${GREEN}[OK] 已配置阿里云镜像源${NC}"
    fi
fi

# 安装基础依赖
echo -e "${BLUE}[步骤 2/8] 安装基础依赖...${NC}"
yum groupinstall -y "Development Tools"
yum install -y \
    wget \
    curl \
    make \
    gcc \
    openssl-devel \
    bzip2-devel \
    libffi-devel \
    zlib-devel \
    libglvnd-glx \
    mesa-libGL \
    glib2 \
    libSM \
    libXext \
    libXrender \
    libgomp

echo -e "${GREEN}[OK] 基础依赖安装完成${NC}"

# 安装 Python 3.11
echo -e "${BLUE}[步骤 3/8] 安装 Python 3.11...${NC}"

if command -v python3.11 &> /dev/null; then
    echo -e "${GREEN}Python 3.11 已安装，跳过${NC}"
else
    cd /usr/src
    PYTHON_VERSION="3.11.9"

    # 下载 Python（使用华为云镜像）
    if [ ! -f "Python-${PYTHON_VERSION}.tgz" ]; then
        echo "正在下载 Python ${PYTHON_VERSION}..."
        wget https://mirrors.huaweicloud.com/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz || \
        wget https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz
    fi

    # 解压编译
    tar xzf Python-${PYTHON_VERSION}.tgz
    cd Python-${PYTHON_VERSION}

    echo "正在编译 Python（这可能需要 5-10 分钟）..."
    ./configure --enable-optimizations --prefix=/usr/local
    make -j$(nproc)
    make altinstall

    echo -e "${GREEN}[OK] Python 3.11 安装完成${NC}"
fi

# 创建软链接
if [ ! -f /usr/bin/python3 ]; then
    ln -sf /usr/local/bin/python3.11 /usr/bin/python3
fi
if [ ! -f /usr/bin/pip3 ]; then
    ln -sf /usr/local/bin/pip3.11 /usr/bin/pip3
fi

python3.11 --version

# 配置 pip 国内镜像
echo -e "${BLUE}[步骤 4/8] 配置 pip 国内镜像...${NC}"
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << EOF
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
[install]
use-mirrors = true
mirrors = https://pypi.tuna.tsinghua.edu.cn
EOF

# 升级 pip
python3.11 -m pip install --upgrade pip

echo -e "${GREEN}[OK] pip 配置完成${NC}"

# 创建应用目录
echo -e "${BLUE}[步骤 5/8] 创建应用目录...${NC}"
APP_DIR="/opt/image-tools"
mkdir -p $APP_DIR
cd $APP_DIR

echo -e "${YELLOW}提示：请将项目文件上传到 ${APP_DIR} 目录${NC}"
echo -e "可以使用以下命令上传："
echo -e "  scp -r image_compress_web/* root@服务器IP:${APP_DIR}/"

# 检查项目文件是否存在
if [ ! -f "backend.py" ]; then
    echo -e "${YELLOW}[警告] 未检测到项目文件${NC}"
    echo "请先上传项目文件后再继续"
    echo ""
    read -p "项目文件已上传？(Y/N): " uploaded
    if [[ $uploaded != "Y" && $uploaded != "y" ]]; then
        echo -e "${YELLOW}安装暂停，上传文件后请重新运行此脚本${NC}"
        exit 0
    fi
fi

# 安装 Python 依赖
echo -e "${BLUE}[步骤 6/8] 安装 Python 依赖...${NC}"
if [ -f "requirements.txt" ]; then
    python3.11 -m pip install -r requirements.txt
    echo -e "${GREEN}[OK] 依赖安装完成${NC}"
else
    echo -e "${YELLOW}[警告] 未找到 requirements.txt${NC}"
fi

# 创建系统服务
echo -e "${BLUE}[步骤 7/8] 创建系统服务...${NC}"

cat > /etc/systemd/system/image-tools.service << EOF
[Unit]
Description=Image Compression Web Tool
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}
ExecStart=/usr/local/bin/python3.11 backend.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable image-tools

echo -e "${GREEN}[OK] 系统服务创建完成${NC}"

# 配置防火墙
echo -e "${BLUE}[步骤 8/8] 配置防火墙...${NC}"

if command -v firewall-cmd &> /dev/null; then
    # firewalld
    firewall-cmd --permanent --add-port=8000/tcp
    firewall-cmd --reload
    echo -e "${GREEN}[OK] 已开放 8000 端口 (firewalld)${NC}"
elif command -v iptables &> /dev/null; then
    # iptables
    iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
    service iptables save
    echo -e "${GREEN}[OK] 已开放 8000 端口 (iptables)${NC}"
fi

# 安装完成
echo ""
echo "=========================================="
echo -e "${GREEN}  安装完成！${NC}"
echo "=========================================="
echo ""
echo "应用目录: ${APP_DIR}"
echo "访问地址: http://服务器IP:8000"
echo ""
echo "服务管理命令："
echo "  启动服务: systemctl start image-tools"
echo "  停止服务: systemctl stop image-tools"
echo "  重启服务: systemctl restart image-tools"
echo "  查看状态: systemctl status image-tools"
echo "  查看日志: journalctl -u image-tools -f"
echo ""

# 询问是否立即启动
read -p "是否立即启动服务？(Y/N): " start_now
if [[ $start_now == "Y" || $start_now == "y" ]]; then
    systemctl start image-tools
    echo -e "${GREEN}服务已启动！${NC}"
    echo "请在浏览器访问: http://服务器IP:8000"

    # 显示服务状态
    sleep 2
    systemctl status image-tools --no-pager
fi

echo ""
echo -e "${GREEN}安装完成！${NC}"
