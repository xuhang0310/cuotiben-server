# Import BaseSettings from pydantic_settings for Pydantic v2 compatibility
# This is required for Python 3.13 environments
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
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 阿里云API配置
    ALIBABA_CLOUD_API_KEY: str = os.getenv("ALIBABA_CLOUD_API_KEY", "")

    # 服务器域名配置
    SERVER_DOMAIN: str = os.getenv("SERVER_DOMAIN", "http://180.76.183.241")

    # SMTP配置 (Tencent Cloud Email)
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.tencent.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")  # 授权码

    # Tencent Cloud Email API配置 (用于模板发送)
    TENCENT_EMAIL_APP_ID: str = os.getenv("TENCENT_EMAIL_APP_ID", "")
    TENCENT_EMAIL_APP_KEY: str = os.getenv("TENCENT_EMAIL_APP_KEY", "")
    TENCENT_EMAIL_SENDER: str = os.getenv("TENCENT_EMAIL_SENDER", "")

    # Pydantic v2 configuration
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()