from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

# 用户基础模型
class UserBase(BaseModel):
    username: str
    email: str

    model_config = ConfigDict(
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        ),
        populate_by_name = True
    )

# 用户创建模型
class UserCreate(UserBase):
    password: str

# 用户更新模型
class UserUpdate(UserBase):
    avatar_url: Optional[str] = None

# 用户数据库模型
class User(UserBase):
    id: int
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        ),
        populate_by_name = True
    )

# 用户登录模型
class UserLogin(BaseModel):
    email: str
    password: str

    model_config = ConfigDict(
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        ),
        populate_by_name = True
    )

# 令牌模型
class Token(BaseModel):
    access_token: str
    token_type: str

    model_config = ConfigDict(
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        ),
        populate_by_name = True
    )

# 令牌数据模型
class TokenData(BaseModel):
    user_id: Optional[int] = None

    model_config = ConfigDict(
        # 为字段名启用驼峰命名转换
        alias_generator = lambda field_name: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split('_'))
        ),
        populate_by_name = True
    )