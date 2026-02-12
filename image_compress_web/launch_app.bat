@echo off
chcp 65001 >nul
echo 图片压缩工具网页版启动器
echo ================================
echo.

REM 检查Python是否已安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python。请先安装Python。
    pause
    exit /b 1
)

REM 检查是否已安装依赖
echo 检查依赖包...
python -c "import fastapi, uvicorn, PIL" 2>nul
if errorlevel 1 (
    echo 安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 依赖安装失败，请检查网络连接或手动安装依赖。
        pause
        exit /b 1
    )
)

REM 检查端口是否被占用
echo 检查端口占用情况...
netstat -an | findstr ":8000 " >nul
if not errorlevel 1 (
    echo 端口8000已被占用，请关闭占用该端口的程序后再试。
    pause
    exit /b 1
)

echo 启动图片压缩工具网页版...
echo 服务将在 http://127.0.0.1:8000 上运行
echo.

REM 启动后端服务并自动打开浏览器
start "" http://127.0.0.1:8000
start /min cmd /k "title 图片压缩工具服务窗口 && python backend.py && pause"

echo.
echo 应用已启动！浏览器将自动打开。
echo 如果浏览器未自动打开，请手动访问 http://127.0.0.1:8000
echo.
echo 要停止服务，请关闭弹出的Python服务窗口或使用任务管理器结束Python进程。
pause