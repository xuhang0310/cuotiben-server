@echo off
chcp 65001 >nul
title 图片压缩工具 - Docker 启动器
echo ==========================================
echo   图片压缩工具 - Docker 一键启动
echo ==========================================
echo.

:: 检查 Docker 是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Docker！
    echo.
    echo 请先安装 Docker Desktop：
    echo https://www.docker.com/products/docker-desktop
    echo.
    echo 国内镜像下载：
    echo https://docker.mirrors.ustc.edu.cn
    echo.
    pause
    exit /b 1
)

:: 检查 Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Docker Compose！
    echo 请更新到最新版 Docker Desktop
    pause
    exit /b 1
)

echo [1/4] 正在检查 Docker 服务...
docker info >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker 服务未启动！
    echo 请启动 Docker Desktop 后重试
    pause
    exit /b 1
)
echo [OK] Docker 服务正常
echo.

echo [2/4] 正在构建 Docker 镜像...
echo 首次构建可能需要 5-10 分钟，请耐心等待...
docker-compose build --no-cache
if errorlevel 1 (
    echo [错误] 镜像构建失败！
    pause
    exit /b 1
)
echo [OK] 镜像构建完成
echo.

echo [3/4] 正在启动服务...
docker-compose up -d
if errorlevel 1 (
    echo [错误] 服务启动失败！
    pause
    exit /b 1
)
echo [OK] 服务已启动
echo.

echo [4/4] 等待服务就绪...
timeout /t 3 /nobreak >nul

echo ==========================================
echo   启动成功！
echo ==========================================
echo.
echo 访问地址：http://localhost:8000
echo.
echo 正在打开浏览器...
start http://localhost:8000

echo.
echo 常用命令：
echo   查看日志：docker-compose logs -f
echo   停止服务：docker-compose down
echo   重启服务：docker-compose restart
echo.
pause
