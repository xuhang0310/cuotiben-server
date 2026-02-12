import os
import json
from pathlib import Path
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from threading import Thread
import time
import logging

# 导入现有的图片压缩工具模块
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'image_compress_tool'))

from image_compressor import compress_image
from file_scanner import scan_images
from file_manager import create_backup_name, safe_replace_original, create_backup_folder
from user_interface import display_progress

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="图片压缩工具网页版", version="1.0.0")

# 添加CORS中间件，允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应指定具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储压缩任务状态
tasks_status = {}

class CompressionSettings(BaseModel):
    directory: str
    target_size: int
    quality: int = 85
    format: str = "保持原格式"
    selected_files: List[str] = []  # 新增：用户选择的文件列表

class TaskStatus(BaseModel):
    task_id: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    progress: float
    total_files: int
    processed_files: int
    skipped_files: int
    message: str

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """返回主页HTML"""
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    if os.path.exists(frontend_path):
        with open(frontend_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>图片压缩工具网页版</h1><p>前端文件未找到</p>")

@app.get("/api/settings")
async def get_settings():
    """获取当前设置"""
    return {
        "default_target_size": 128,
        "default_quality": 85,
        "supported_formats": ["保持原格式", "JPEG", "PNG", "WEBP"]
    }

@app.get("/api/default-path")
async def get_default_path():
    """获取系统默认下载路径"""
    import os
    from pathlib import Path
    
    # 获取系统默认下载文件夹路径
    download_path = str(Path.home() / "Downloads")
    
    return {"default_path": download_path}


@app.get("/api/preview")
async def get_image_preview(file: str):
    """获取图片预览"""
    import base64
    from fastapi.responses import Response
    
    logger.info(f"请求预览图片: {file}")
    
    # 验证文件路径，防止路径遍历攻击
    if '..' in file or not file.startswith(('C:', '/')):
        logger.warning(f"无效的文件路径: {file}")
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    # 检查文件是否存在
    if not os.path.exists(file):
        logger.error(f"文件不存在: {file}")
        raise HTTPException(status_code=404, detail="File not found")
    
    # 检查文件扩展名是否为图片格式
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff']
    if not any(file.lower().endswith(ext) for ext in valid_extensions):
        logger.error(f"文件不是有效的图片格式: {file}")
        raise HTTPException(status_code=400, detail="File is not a valid image")
    
    try:
        # 读取图片文件
        logger.debug(f"尝试读取文件: {file}")
        with open(file, 'rb') as f:
            image_data = f.read()
        
        # 获取文件的MIME类型
        ext = os.path.splitext(file)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.bmp': 'image/bmp',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.tiff': 'image/tiff'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')
        
        logger.info(f"成功返回图片预览: {file}")
        return Response(content=image_data, media_type=mime_type)
    except PermissionError:
        logger.error(f"权限不足，无法访问文件: {file}")
        raise HTTPException(status_code=403, detail="Permission denied to access the file")
    except Exception as e:
        logger.error(f"读取图片时出错 {file}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading image: {str(e)}")

@app.post("/api/folder/scan")
async def scan_folder(settings: CompressionSettings):
    """扫描文件夹中的图片文件（非递归）"""
    logger.info(f"开始扫描文件夹: {settings.directory}")
    
    try:
        if not os.path.isdir(settings.directory):
            logger.error(f"指定的路径不是有效的文件夹: {settings.directory}")
            raise HTTPException(status_code=400, detail=f"指定的路径不是有效的文件夹: {settings.directory}")
        
        # 只扫描当前文件夹，不递归扫描子文件夹
        from pathlib import Path
        
        # 支持的图片格式
        supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif'}
        logger.info(f"支持的图片格式: {supported_formats}")
        
        files_info = []
        
        try:
            # 获取文件夹中的所有项目
            all_items = os.listdir(settings.directory)
            logger.info(f"文件夹 '{settings.directory}' 中共有 {len(all_items)} 个项目")
            
            # 遏当前文件夹中的文件
            for file_name in all_items:
                file_path = os.path.join(settings.directory, file_name)
                logger.debug(f"检查项目: {file_name}, 路径: {file_path}")
                
                # 检查是否是文件（而不是子文件夹）
                if os.path.isfile(file_path):
                    logger.debug(f"  是文件，检查扩展名")
                    file_ext = Path(file_name).suffix.lower()
                    logger.debug(f"  文件扩展名: {file_ext}")
                    
                    # 检查文件扩展名是否是支持的图片格式
                    if file_ext in supported_formats:
                        logger.info(f"  找到支持的图片文件: {file_name}")
                        try:
                            size_kb = os.path.getsize(file_path) // 1024
                            logger.debug(f"  文件大小: {size_kb}KB")
                            files_info.append({
                                "path": file_path,
                                "name": file_name,
                                "size_kb": size_kb
                            })
                            logger.info(f"  已添加文件到列表: {file_name}")
                        except PermissionError:
                            # 如果无法访问某个文件，跳过它
                            logger.warning(f"Permission denied for file: {file_path}")
                            continue
                        except OSError as e:
                            # 如果文件有问题，跳过它
                            logger.warning(f"Error accessing file {file_path}: {e}")
                            continue
                    else:
                        logger.debug(f"  文件扩展名 {file_ext} 不在支持的格式列表中，跳过")
                else:
                    logger.debug(f"  是文件夹，跳过")
                    
        except PermissionError as e:
            logger.error(f"没有权限访问文件夹: {settings.directory}, 错误: {e}")
            raise HTTPException(status_code=403, detail=f"没有权限访问文件夹: {settings.directory}")
        except Exception as e:
            logger.error(f"访问文件夹时出错: {e}")
            raise HTTPException(status_code=500, detail=f"访问文件夹时出错: {str(e)}")
        
        logger.info(f"扫描完成，找到 {len(files_info)} 个图片文件")
        return {
            "folder_path": settings.directory,
            "total_files": len(files_info),
            "files": files_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"扫描文件夹时出错: {e}")
        raise HTTPException(status_code=500, detail=f"扫描文件夹时出错: {str(e)}")

@app.post("/api/compress")
async def start_compression(settings: CompressionSettings):
    """开始压缩任务"""
    task_id = f"task_{int(time.time())}"
    
    # 初始化任务状态
    tasks_status[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0,
        "total_files": 0,
        "processed_files": 0,
        "skipped_files": 0,
        "message": "任务初始化中"
    }
    
    # 在后台线程中执行压缩任务
    thread = Thread(target=run_compression_task, args=(task_id, settings))
    thread.start()
    
    return {"task_id": task_id}

def run_compression_task(task_id: str, settings: CompressionSettings):
    """在后台线程中执行压缩任务"""
    try:
        # 更新任务状态
        tasks_status[task_id]["status"] = "processing"
        tasks_status[task_id]["message"] = "正在准备压缩任务..."
        
        # 获取要处理的文件列表
        # 如果用户选择了特定文件，则只处理这些文件
        # 否则处理文件夹中的所有图片文件
        if settings.selected_files:
            image_files = settings.selected_files
            total_files = len(image_files)
        else:
            # 扫描当前文件夹（非递归）
            from pathlib import Path
            
            # 支持的图片格式
            supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif'}
            
            image_files = []
            
            # 遏当前文件夹中的文件
            for file_name in os.listdir(settings.directory):
                file_path = os.path.join(settings.directory, file_name)
                
                # 检查是否是文件（而不是子文件夹）
                if os.path.isfile(file_path):
                    file_ext = Path(file_name).suffix.lower()
                    
                    # 检查文件扩展名是否是支持的图片格式
                    if file_ext in supported_formats:
                        image_files.append(file_path)
            
            total_files = len(image_files)
        
        tasks_status[task_id]["total_files"] = total_files
        
        processed_files = 0
        skipped_files = 0
        compressed_files = []
        
        # 遍历图片文件进行压缩
        for i, image_path in enumerate(image_files):
            # 检查文件是否存在
            if not os.path.exists(image_path):
                tasks_status[task_id]["message"] = f"跳过: {os.path.basename(image_path)} (文件不存在)"
                skipped_files += 1
                tasks_status[task_id]["skipped_files"] = skipped_files
                continue
            
            # 检查原始文件大小
            original_size = os.path.getsize(image_path) // 1024
            
            # 如果原始文件已经小于目标大小，跳过处理
            if original_size <= settings.target_size:
                tasks_status[task_id]["message"] = f"跳过: {os.path.basename(image_path)} (原大小 {original_size}KB <= 目标大小 {settings.target_size}KB)"
                skipped_files += 1
                tasks_status[task_id]["skipped_files"] = skipped_files
                continue
            
            # 更新进度
            tasks_status[task_id]["message"] = f"正在处理: {os.path.basename(image_path)}"
            
            # 创建备份文件名（带_compress后缀）
            backup_path = create_backup_name(image_path)
            
            # 压缩图片
            success = compress_image(
                input_path=image_path,
                output_path=backup_path,
                target_size_kb=settings.target_size,
                quality=settings.quality,
                target_format=settings.format if settings.format != "保持原格式" else None
            )
            
            if success:
                compressed_files.append(backup_path)
                processed_files += 1
                tasks_status[task_id]["processed_files"] = processed_files
            else:
                # 如果压缩失败，删除可能创建的不完整文件
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                processed_files += 1  # 失败也算处理过
                tasks_status[task_id]["processed_files"] = processed_files
            
            # 更新进度百分比
            progress = ((i + 1) / total_files) * 100
            tasks_status[task_id]["progress"] = progress
        
        # 更新最终状态
        tasks_status[task_id]["status"] = "completed"
        tasks_status[task_id]["message"] = f"压缩完成！共处理 {processed_files} 个文件，跳过 {skipped_files} 个小于目标大小的文件"
        
        # 询问是否要移动原图到备份文件夹并重命名压缩图
        # 在实际应用中，这里可能需要用户确认
        # 为了演示目的，我们直接执行操作
        if processed_files > 0:
            tasks_status[task_id]["message"] = "正在移动原始文件到备份文件夹..."
            
            successful_replacements = 0
            for compress_path in compressed_files:
                if safe_replace_original(compress_path):
                    successful_replacements += 1
            
            tasks_status[task_id]["message"] = f"处理完成！成功处理 {successful_replacements} 个文件，原始文件已保存在备份文件夹中"
        
    except Exception as e:
        tasks_status[task_id]["status"] = "failed"
        tasks_status[task_id]["message"] = f"处理失败: {str(e)}"

@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in tasks_status:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return tasks_status[task_id]

# 挂载前端静态文件
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)