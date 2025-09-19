from pydantic import BaseModel, ConfigDict
from typing import TypeVar, Generic, Optional, Any

T = TypeVar('T')

class SuccessResponse(BaseModel, Generic[T]):
    """统一的成功响应模型"""
    success: bool = True
    data: T
    
    model_config = ConfigDict(
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        )
    )

class ErrorResponse(BaseModel):
    """统一的错误响应模型"""
    success: bool = False
    error: Optional[str] = None
    message: str
    
    model_config = ConfigDict(
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        )
    )