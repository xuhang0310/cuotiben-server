@echo off
echo Starting Image Compression Web Tool in minimized mode...
echo.

REM 检查是否已安装依赖
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM 启动后端服务并自动打开浏览器
echo Starting server on http://127.0.0.1:8000
start "" http://127.0.0.1:8000
start /min python backend.py