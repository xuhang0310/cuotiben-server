#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建数据库表结构
"""

import sys
import os

# 添加项目路径到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import engine, Base
from app.models.user import User
from app.models.subject import Subject
from app.models.question_type import QuestionType
from app.models.question import Question
from app.models.question_option import QuestionOption
from app.models.tag import Tag
from app.models.question_tag import QuestionTag
from app.models.practice_record import PracticeRecord
from app.models.user_settings import UserSettings

def init_database():
    """初始化数据库表结构"""
    print("🔧 初始化数据库表结构...")
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    print("✅ 数据库表结构初始化完成")
    print("📋 已创建的表:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")

if __name__ == "__main__":
    init_database()