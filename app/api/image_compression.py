from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
import io

from app.utils.image_compression import (
    compress_image_to_size,
    resize_image_by_percentage,
    get_image_info,
    compress_image_by_dimensions
)

router = APIRouter(prefix="/image-compression", tags=["image-compression"])


@router.post("/compress-to-size/")
async def compress_image_to_target_size(
    file: UploadFile = File(...),
    target_size_kb: int = Query(default=512, ge=1, le=10240, description="目标文件大小（KB），范围1-10240"),
    quality_step: int = Query(default=5, ge=1, le=20, description="质量调整步长，范围1-20"),
    max_iterations: int = Query(default=20, ge=5, le=50, description="最大迭代次数，范围5-50")
):
    """
    将上传的图片压缩至指定大小
    
    Args:
        file: 要压缩的图片文件
        target_size_kb: 目标文件大小（KB），默认512KB
        quality_step: 质量调整步长，默认5
        max_iterations: 最大迭代次数，默认20
    
    Returns:
        StreamingResponse: 压缩后的图片文件流
    """
    try:
        # 验证文件类型
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="请上传有效的图片文件")
        
        # 读取文件内容
        file_content = await file.read()
        
        # 压缩图片
        compressed_image_bytes = compress_image_to_size(
            image_input=file_content,
            target_size_kb=target_size_kb,
            quality_step=quality_step,
            max_iterations=max_iterations
        )
        
        # 获取原始文件扩展名
        file_extension = file.filename.split(".")[-1].lower() if file.filename else "jpg"
        if file_extension not in ["jpg", "jpeg", "png", "gif", "bmp", "webp"]:
            file_extension = "jpg"  # 默认使用jpg
        
        # 创建响应
        response = StreamingResponse(io.BytesIO(compressed_image_bytes), media_type=f"image/{file_extension}")
        response.headers["Content-Disposition"] = f"attachment; filename=compressed_{target_size_kb}kb.{file_extension}"
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片压缩失败: {str(e)}")


@router.post("/resize-by-percentage/")
async def resize_image_percentage(
    file: UploadFile = File(...),
    scale_factor: float = Query(default=0.8, ge=0.1, le=1.0, description="缩放比例，范围0.1-1.0")
):
    """
    按百分比缩放图片
    
    Args:
        file: 要缩放的图片文件
        scale_factor: 缩放比例，如0.8表示缩小到80%
    
    Returns:
        StreamingResponse: 缩放后的图片文件流
    """
    try:
        # 验证文件类型
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="请上传有效的图片文件")
        
        # 读取文件内容
        file_content = await file.read()
        
        # 按比例缩放图片
        resized_image_bytes = resize_image_by_percentage(
            image_input=file_content,
            scale_factor=scale_factor
        )
        
        # 获取原始文件扩展名
        file_extension = file.filename.split(".")[-1].lower() if file.filename else "jpg"
        if file_extension not in ["jpg", "jpeg", "png", "gif", "bmp", "webp"]:
            file_extension = "jpg"  # 默认使用jpg
        
        # 创建响应
        response = StreamingResponse(io.BytesIO(resized_image_bytes), media_type=f"image/{file_extension}")
        response.headers["Content-Disposition"] = f"attachment; filename=scaled_{int(scale_factor*100)}percent.{file_extension}"
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片缩放失败: {str(e)}")


@router.post("/compress-by-dimensions/")
async def compress_image_dimensions(
    file: UploadFile = File(...),
    max_width: int = Query(default=1920, ge=100, le=10000, description="最大宽度，范围100-10000"),
    max_height: int = Query(default=1080, ge=100, le=10000, description="最大高度，范围100-10000")
):
    """
    按最大尺寸限制压缩图片
    
    Args:
        file: 要压缩的图片文件
        max_width: 最大宽度，默认1920
        max_height: 最大高度，默认1080
    
    Returns:
        StreamingResponse: 压缩后的图片文件流
    """
    try:
        # 验证文件类型
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="请上传有效的图片文件")
        
        # 读取文件内容
        file_content = await file.read()
        
        # 按尺寸压缩图片
        compressed_image_bytes = compress_image_by_dimensions(
            image_input=file_content,
            max_width=max_width,
            max_height=max_height
        )
        
        # 获取原始文件扩展名
        file_extension = file.filename.split(".")[-1].lower() if file.filename else "jpg"
        if file_extension not in ["jpg", "jpeg", "png", "gif", "bmp", "webp"]:
            file_extension = "jpg"  # 默认使用jpg
        
        # 创建响应
        response = StreamingResponse(io.BytesIO(compressed_image_bytes), media_type=f"image/{file_extension}")
        response.headers["Content-Disposition"] = f"attachment; filename=dimensions_limited_{max_width}x{max_height}.{file_extension}"
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片按尺寸压缩失败: {str(e)}")


@router.post("/info/")
async def get_image_information(file: UploadFile = File(...)):
    """
    获取图片信息
    
    Args:
        file: 要分析的图片文件
    
    Returns:
        dict: 包含图片信息的字典
    """
    try:
        # 验证文件类型
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="请上传有效的图片文件")
        
        # 读取文件内容
        file_content = await file.read()
        
        # 获取图片信息
        image_info = get_image_info(image_input=file_content)
        
        # 移除PIL Image对象，因为它不能被序列化
        del image_info['original_object']
        
        return {
            "success": True,
            "info": image_info
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图片信息失败: {str(e)}")