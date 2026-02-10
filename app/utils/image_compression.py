"""
图片压缩工具
用于将图片压缩至指定大小（默认512KB）
"""

import os
import io
from typing import Union, Tuple
from PIL import Image, ImageOps
from PIL.Image import Resampling


def compress_image_to_size(
    image_input: Union[str, bytes, io.BytesIO], 
    target_size_kb: int = 512,
    quality_step: int = 5,
    max_iterations: int = 20
) -> bytes:
    """
    将图片压缩至目标大小
    
    Args:
        image_input: 图片输入，可以是文件路径、字节数据或BytesIO对象
        target_size_kb: 目标大小（KB），默认512KB
        quality_step: JPEG质量调整步长，默认5
        max_iterations: 最大迭代次数，默认20
    
    Returns:
        bytes: 压缩后的图片字节数据
    """
    # 打开图片
    if isinstance(image_input, str):
        # 文件路径
        with Image.open(image_input) as img:
            img = img.copy()  # 避免关闭原文件
    elif isinstance(image_input, bytes):
        # 字节数据
        img = Image.open(io.BytesIO(image_input))
    elif isinstance(image_input, io.IOBase):
        # BytesIO对象
        img = Image.open(image_input)
        image_input.seek(0)  # 重置指针
    else:
        raise ValueError("不支持的图片输入类型")
    
    # 确保图像是RGB模式（对于JPEG）或RGBA模式（对于PNG）
    if img.mode in ('RGBA', 'LA', 'P'):
        # 如果图片有透明度，转换为RGBA
        if img.mode == 'P':
            # 先转换为RGBA以保留透明度
            img = img.convert('RGBA')
        
        # 检查是否有透明像素
        alpha_channel = img.split()[-1] if img.mode == 'RGBA' else None
        has_transparency = alpha_channel and alpha_channel.getbbox() is not None
        
        if has_transparency:
            # 有透明度，保持为PNG
            output_format = 'PNG'
        else:
            # 没有透明度，转换为RGB以适应JPEG
            img = img.convert('RGB')
            output_format = 'JPEG'
    else:
        # 其他模式转换为RGB
        img = img.convert('RGB')
        output_format = 'JPEG'

    # 初始压缩参数
    quality = 95  # 初始质量
    scale_factor = 1.0  # 初始缩放因子
    
    # 迭代压缩直到达到目标大小或达到最大迭代次数
    iteration = 0
    while iteration < max_iterations:
        # 创建输出缓冲区
        output_buffer = io.BytesIO()
        
        # 如果需要缩放，则先缩放
        if scale_factor < 1.0:
            new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
            resized_img = img.resize(new_size, Resampling.LANCZOS)
        else:
            resized_img = img
            
        # 保存图片
        if output_format == 'JPEG':
            resized_img.save(
                output_buffer, 
                format='JPEG', 
                quality=min(quality, 95), 
                optimize=True
            )
        else:  # PNG
            resized_img.save(
                output_buffer, 
                format='PNG',
                optimize=True
            )
            
        compressed_size_kb = len(output_buffer.getvalue()) / 1024
        
        # 检查是否达到目标大小
        if compressed_size_kb <= target_size_kb:
            return output_buffer.getvalue()
        
        # 如果当前质量已经是最低，尝试缩小尺寸
        if quality <= 10:
            # 减小缩放比例
            scale_factor *= 0.9
            if scale_factor < 0.1:  # 防止过度缩小
                break
        else:
            # 降低质量
            quality -= quality_step
            
        iteration += 1
    
    # 如果经过多次迭代仍未达到目标大小，返回最后一次压缩结果
    return output_buffer.getvalue()


def resize_image_by_percentage(
    image_input: Union[str, bytes, io.BytesIO], 
    scale_factor: float
) -> bytes:
    """
    按百分比缩放图片
    
    Args:
        image_input: 图片输入
        scale_factor: 缩放因子 (例如 0.8 表示缩小到80%)
    
    Returns:
        bytes: 缩放后的图片字节数据
    """
    # 打开图片
    if isinstance(image_input, str):
        with Image.open(image_input) as img:
            img = img.copy()
    elif isinstance(image_input, bytes):
        img = Image.open(io.BytesIO(image_input))
    elif isinstance(image_input, io.IOBase):
        img = Image.open(image_input)
        image_input.seek(0)
    else:
        raise ValueError("不支持的图片输入类型")
    
    # 计算新尺寸
    new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
    
    # 缩放图片
    resized_img = img.resize(new_size, Resampling.LANCZOS)
    
    # 保存到字节流
    output_buffer = io.BytesIO()
    if img.mode in ('RGBA', 'LA', 'P'):
        # 检查透明度
        alpha_channel = img.split()[-1] if img.mode == 'RGBA' else None
        has_transparency = alpha_channel and alpha_channel.getbbox() is not None
        
        if has_transparency:
            resized_img.save(output_buffer, format='PNG', optimize=True)
        else:
            resized_img = resized_img.convert('RGB')
            resized_img.save(output_buffer, format='JPEG', optimize=True)
    else:
        resized_img.save(output_buffer, format='JPEG', optimize=True)
    
    return output_buffer.getvalue()


def get_image_info(image_input: Union[str, bytes, io.BytesIO]) -> dict:
    """
    获取图片信息
    
    Args:
        image_input: 图片输入
    
    Returns:
        dict: 包含图片信息的字典
    """
    # 打开图片
    if isinstance(image_input, str):
        img = Image.open(image_input)
        size_kb = os.path.getsize(image_input) / 1024
    elif isinstance(image_input, bytes):
        img = Image.open(io.BytesIO(image_input))
        size_kb = len(image_input) / 1024
    elif isinstance(image_input, io.IOBase):
        pos = image_input.tell()
        img = Image.open(image_input)
        image_input.seek(pos)  # 恢复原始位置
        pos_end = image_input.tell()
        image_input.seek(pos)  # 恢复原始位置
        size_bytes = pos_end - pos
        size_kb = size_bytes / 1024
    else:
        raise ValueError("不支持的图片输入类型")
    
    return {
        'width': img.width,
        'height': img.height,
        'mode': img.mode,
        'format': img.format,
        'size_kb': round(size_kb, 2),
        'original_object': img
    }


def compress_image_by_dimensions(
    image_input: Union[str, bytes, io.BytesIO],
    max_width: int = 1920,
    max_height: int = 1080
) -> bytes:
    """
    按最大尺寸限制压缩图片
    
    Args:
        image_input: 图片输入
        max_width: 最大宽度
        max_height: 最大高度
    
    Returns:
        bytes: 压缩后的图片字节数据
    """
    # 打开图片
    if isinstance(image_input, str):
        with Image.open(image_input) as img:
            img = img.copy()
    elif isinstance(image_input, bytes):
        img = Image.open(io.BytesIO(image_input))
    elif isinstance(image_input, io.IOBase):
        img = Image.open(image_input)
        image_input.seek(0)
    else:
        raise ValueError("不支持的图片输入类型")
    
    # 按比例缩放到最大尺寸内
    img.thumbnail((max_width, max_height), Resampling.LANCZOS)
    
    # 保存到字节流
    output_buffer = io.BytesIO()
    if img.mode in ('RGBA', 'LA', 'P'):
        # 检查透明度
        alpha_channel = img.split()[-1] if img.mode == 'RGBA' else None
        has_transparency = alpha_channel and alpha_channel.getbbox() is not None
        
        if has_transparency:
            img.save(output_buffer, format='PNG', optimize=True)
        else:
            img = img.convert('RGB')
            img.save(output_buffer, format='JPEG', optimize=True)
    else:
        img.save(output_buffer, format='JPEG', optimize=True)
    
    return output_buffer.getvalue()