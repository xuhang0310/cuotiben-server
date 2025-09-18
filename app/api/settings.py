from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

def safe_str(value):
    """安全地将值转换为字符串"""
    if value is None:
        return None
    return str(value)

def safe_int(value):
    """安全地将值转换为整数"""
    if value is None:
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0

def safe_bool(value):
    """安全地将值转换为布尔值"""
    if value is None:
        return False
    return bool(value)

@router.get("/")
def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 在实际项目中，这里需要从数据库获取用户的设置
    # 目前返回模拟数据
    settings_data = {
        "study_goal": 10,
        "preferred_subjects": ["数学", "语文", "英语"],
        "difficulty": "medium",
        "theme": "light",
        "language": "zh-CN",
        "font_size": "medium",
        "enable_notifications": True,
        "study_reminder": True,
        "reminder_time": "20:00:00",
        "auto_backup": True,
        "backup_frequency": "daily"
    }
    
    return {
        "success": True,
        "data": {
            "settings": settings_data
        }
    }

@router.put("/")
def update_settings(
    settings_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 在实际项目中，这里需要更新数据库中的用户设置
    # 目前只是返回接收到的数据
    return {
        "success": True,
        "data": {
            "settings": settings_data
        }
    }