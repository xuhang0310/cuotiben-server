from typing import Optional, Any
from datetime import datetime

def safe_str(value: Any) -> str:
    """安全地将值转换为字符串"""
    if value is None:
        return ""
    return str(value)

def safe_bool(value: Any) -> bool:
    """安全地将值转换为布尔值"""
    if value is None:
        return False
    return bool(value)

def safe_int(value: Any) -> int:
    """安全地将值转换为整数"""
    if value is None:
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0

def safe_datetime(value: Any) -> Optional[datetime]:
    """安全地处理日期时间值"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return None