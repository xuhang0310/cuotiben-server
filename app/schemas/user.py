from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# 用户基础模型
class UserBase(BaseModel):
    username: str
    email: str

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

    class Config:
        from_attributes = True

# 用户登录模型
class UserLogin(BaseModel):
    email: str
    password: str

# 令牌模型
class Token(BaseModel):
    access_token: str
    token_type: str

# 令牌数据模型
class TokenData(BaseModel):
    user_id: Optional[int] = None