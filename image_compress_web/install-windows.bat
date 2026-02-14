@echo off
chcp 65001 >nul
title 图片压缩工具 - Windows 安装向导
color 0A
echo ==========================================
echo   图片压缩工具 - Windows 安装向导
echo ==========================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if errorlevel 1 (
    echo [提示] 建议以管理员身份运行以获得最佳体验
echo.
    pause
)

:: 步骤1：检查 Python
echo [步骤 1/5] 正在检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [警告] 未检测到 Python！
    echo.
    echo 请按以下步骤安装 Python 3.11：
    echo.
    echo 1. 访问 https://www.python.org/downloads/
    echo 2. 下载 Python 3.11.x（64-bit）
    echo 3. 运行安装程序，**务必勾选 "Add Python to PATH"**
    echo 4. 选择 "Install Now"
    echo.
    echo 或使用国内镜像下载：
    echo https://mirrors.aliyun.com/pypi/simple/python/3.11.9/
    echo.
    echo 安装完成后，重新运行此脚本。
    echo.
    start https://www.python.org/downloads/release/python-3119/
    pause
    exit /b 1
)

for /f "tokens=*" %%a in ('python --version') do set PYTHON_VERSION=%%a
echo [OK] 检测到 %PYTHON_VERSION%
echo.

:: 步骤2：配置 pip 国内镜像
echo [步骤 2/5] 正在配置 pip 国内镜像...
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn >nul 2>&1
echo [OK] 已配置清华镜像源
echo.

:: 步骤3：升级 pip
echo [步骤 3/5] 正在升级 pip...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
echo [OK] pip 升级完成
echo.

:: 步骤4：安装依赖
echo [步骤 4/5] 正在安装依赖包...
echo 这可能需要几分钟，请耐心等待...
echo.

pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [错误] 依赖安装失败！
    echo 请检查网络连接，或稍后再试。
    pause
    exit /b 1
)
echo [OK] 依赖安装完成
echo.

:: 步骤5：检查端口
echo [步骤 5/5] 正在检查端口占用...
netstat -an | findstr ":8000" >nul
if not errorlevel 1 (
    echo [警告] 端口 8000 已被占用！
    echo 请关闭占用该端口的程序后重试。
    pause
    exit /b 1
)
echo [OK] 端口 8000 可用
echo.

:: 安装完成
echo ==========================================
echo   安装完成！
echo ==========================================
echo.
echo 现在可以启动服务了：
echo.
echo 方式1 - 双击运行 start.bat
echo 方式2 - 在命令行执行: python backend.py
echo.
echo 启动后，在浏览器访问: http://127.0.0.1:8000
echo.

:: 询问是否立即启动
set /p START_NOW=是否立即启动服务？(Y/N):
if /i "%START_NOW%"=="Y" (
    echo.
    echo 正在启动服务...
    start http://127.0.0.1:8000
    python backend.py
) else (
    echo.
    echo 安装完成！下次可双击 start.bat 启动服务。
    pause
)
