# PowerShell脚本：启动图片压缩工具网页版
# 文件名: launch_app.ps1

# 检查Python是否已安装
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "错误: 未找到Python。请先安装Python。" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

# 检查依赖
Write-Host "检查依赖包..." -ForegroundColor Yellow
$dependencies = @("fastapi", "uvicorn", "PIL")
$missing_deps = @()

foreach ($dep in $dependencies) {
    $result = python -c "import $dep" 2>$null
    if ($LASTEXITCODE -ne 0) {
        $missing_deps += $dep
    }
}

# 如果有缺失的依赖，安装它们
if ($missing_deps.Count -gt 0) {
    Write-Host "安装缺失的依赖包..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "依赖安装失败，请检查网络连接或手动安装依赖。" -ForegroundColor Red
        Read-Host "按任意键退出"
        exit 1
    }
}

# 检查端口是否被占用
$portCheck = netstat -an | Select-String ":8000 "
if ($portCheck) {
    Write-Host "端口8000已被占用，请关闭占用该端口的程序后再试。" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

Write-Host "启动图片压缩工具网页版..." -ForegroundColor Green
Write-Host "服务将在 http://127.0.0.1:8000 上运行" -ForegroundColor Cyan

# 启动后端服务（在后台运行）
Start-Process -FilePath "python" -ArgumentList "backend.py" -WorkingDirectory "$PSScriptRoot"

# 等待几秒让服务器启动
Start-Sleep -Seconds 3

# 打开浏览器访问应用
Start-Process "http://127.0.0.1:8000"

Write-Host ""
Write-Host "应用已启动！浏览器将自动打开。" -ForegroundColor Green
Write-Host "如果浏览器未自动打开，请手动访问 http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "要停止服务，请关闭Python后端窗口或使用任务管理器结束Python进程。" -ForegroundColor Magenta