from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # 数据库配置
    DB_HOST: str = os.getenv("DB_HOST", "180.76.183.241")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "xp@2025")
    DB_NAME: str = os.getenv("DB_NAME", "cuotiben")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 服务器配置
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()