from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
from app.utils.image_upload import ImageUploadUtil

router = APIRouter(prefix="/upload", tags=["upload"])

# 创建图片上传工具实例
image_uploader = ImageUploadUtil(storage_path="uploads/images", base_url="/static")


@router.post("/image/")
async def upload_image(
    file: UploadFile = File(...),
    max_width: Optional[int] = 1920,
    max_height: Optional[int] = 1080
):
    """
    上传图片文件
    - **file**: 要上传的图片文件
    - **max_width**: 图片最大宽度，默认1920
    - **max_height**: 图片最大高度，默认1080
    """
    try:
        # 使用图片上传工具上传图片
        image_url = await image_uploader.upload_image(
            file=file,
            max_width=max_width,
            max_height=max_height
        )
        return {
            "success": True,
            "message": "图片上传成功",
            "url": image_url,
            "original_filename": file.filename
        }
    except HTTPException as e:
        # 重新抛出HTTP异常
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.delete("/image/")
async def delete_image(url: str):
    """
    删除图片文件
    - **url**: 要删除的图片URL
    """
    try:
        success = image_uploader.delete_image(url)
        if success:
            return {
                "success": True,
                "message": "图片删除成功"
            }
        else:
            raise HTTPException(status_code=404, detail="图片不存在或无法删除")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")