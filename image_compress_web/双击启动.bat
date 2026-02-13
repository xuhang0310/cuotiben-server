@echo off
chcp 65001 >nul
title 图片压缩工具
color 0B
echo ==========================================
echo   图片压缩工具
echo ==========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python！
    echo.
    echo 请先运行 install-windows.bat 进行安装
    echo.
    pause
    exit /b 1
)

:: 检查依赖
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [提示] 首次运行，正在安装依赖...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo.
)

echo 正在启动服务...
echo 稍后浏览器将自动打开
echo.

:: 在后台启动服务
start /b python backend.py

:: 等待服务启动
timeout /t 3 /nobreak >nul

:: 打开浏览器
start http://127.0.0.1:8000

echo 服务已启动！
echo 访问地址：http://127.0.0.1:8000
echo.
echo 不要关闭此窗口，最小化即可
echo 关闭此窗口将停止服务
echo.
pause
