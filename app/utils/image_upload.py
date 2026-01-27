import os
import uuid
from datetime import datetime
from typing import Optional
from fastapi import UploadFile, HTTPException
from PIL import Image
import io


class ImageUploadUtil:
    """
    图片上传工具类
    支持设置存储路径，上传完成后返回可通过HTTP协议访问的网络地址
    """

    def __init__(self, storage_path: str = "uploads/images", base_url: str = "/static"):
        """
        初始化图片上传工具
        
        Args:
            storage_path: 图片存储的相对路径，默认为 uploads/images
            base_url: 访问图片的基础URL，默认为 /static
        """
        self.storage_path = storage_path
        self.base_url = base_url.rstrip('/')
        self.allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
        self.max_file_size = 10 * 1024 * 1024  # 10MB

        # 创建存储目录
        self._ensure_storage_directory()

    def _ensure_storage_directory(self):
        """确保存储目录存在"""
        full_path = os.path.join("app", self.storage_path)
        os.makedirs(full_path, exist_ok=True)

    def _validate_file(self, file: UploadFile) -> bool:
        """
        验证上传的文件
        
        Args:
            file: 上传的文件
            
        Returns:
            bool: 文件是否有效
        """
        if not file.filename:
            return False

        # 检查文件扩展名
        _, ext = os.path.splitext(file.filename.lower())
        if ext not in self.allowed_extensions:
            return False

        # 检查文件大小
        if hasattr(file, 'size') and file.size and file.size > self.max_file_size:
            return False

        return True

    def _generate_filename(self, original_filename: str) -> str:
        """
        生成唯一的文件名
        
        Args:
            original_filename: 原始文件名
            
        Returns:
            str: 生成的新文件名
        """
        name, ext = os.path.splitext(original_filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{timestamp}_{unique_id}{ext.lower()}"

    def _resize_image(self, file: UploadFile, max_width: int = 1920, max_height: int = 1080) -> bytes:
        """
        调整图片大小以节省存储空间
        
        Args:
            file: 上传的图片文件
            max_width: 最大宽度
            max_height: 最大高度
            
        Returns:
            bytes: 调整大小后的图片字节数据
        """
        # 读取文件内容
        content = file.file.read()
        file.file.seek(0)  # 重置文件指针

        # 使用PIL打开图片
        img = Image.open(io.BytesIO(content))

        # 调整图片大小
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        # 保存到字节流
        output = io.BytesIO()
        img.save(output, format=img.format)
        output.seek(0)

        return output.getvalue()

    async def upload_image(self, file: UploadFile, max_width: int = 1920, max_height: int = 1080) -> str:
        """
        上传图片文件
        
        Args:
            file: 上传的图片文件
            max_width: 最大宽度（默认1920）
            max_height: 最大高度（默认1080）
            
        Returns:
            str: 图片的访问URL
            
        Raises:
            HTTPException: 文件验证失败或上传过程中发生错误
        """
        # 验证文件
        if not self._validate_file(file):
            raise HTTPException(
                status_code=400,
                detail=f"无效的文件格式或文件过大。支持的格式: {', '.join(self.allowed_extensions)}"
            )

        # 生成唯一文件名
        filename = self._generate_filename(file.filename)
        filepath = os.path.join("app", self.storage_path, filename)

        try:
            # 调整图片大小
            resized_image_bytes = self._resize_image(file, max_width, max_height)

            # 保存文件
            with open(filepath, "wb") as f:
                f.write(resized_image_bytes)

            # 生成访问URL
            url_path = f"{self.base_url}/{self.storage_path}/{filename}".replace("//", "/")
            return url_path

        except Exception as e:
            # 如果保存失败，删除可能已创建的文件
            if os.path.exists(filepath):
                os.remove(filepath)
            raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

    def delete_image(self, url: str) -> bool:
        """
        删除图片文件
        
        Args:
            url: 图片的访问URL
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 从URL提取文件路径
            if url.startswith(self.base_url):
                relative_path = url[len(self.base_url):].lstrip('/')
                filepath = os.path.join("app", relative_path)
                
                if os.path.exists(filepath):
                    os.remove(filepath)
                    return True
            return False
        except Exception:
            return False

    def get_full_path(self, url: str) -> Optional[str]:
        """
        获取图片的完整文件路径
        
        Args:
            url: 图片的访问URL
            
        Returns:
            Optional[str]: 完整文件路径，如果URL无效则返回None
        """
        if url.startswith(self.base_url):
            relative_path = url[len(self.base_url):].lstrip('/')
            return os.path.join("app", relative_path)
        return None