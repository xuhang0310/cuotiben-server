from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.question import Question
from app.models.practice_record import PracticeRecord
from app.models.subject import Subject
from app.schemas.response import SuccessResponse

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

def safe_float(value):
    """安全地将值转换为浮点数"""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def safe_bool(value):
    """安全地将值转换为布尔值"""
    if value is None:
        return False
    return bool(value)

@router.get("/")
def get_statistics(
    time_range: str = "week",
    subject: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 获取基础统计数据
    total_questions = db.query(Question).filter(Question.user_id == current_user.id).count()
    
    practice_records = db.query(PracticeRecord).filter(
        PracticeRecord.user_id == current_user.id
    ).all()
    
    total_practiced = len(practice_records)
    total_attempts = total_practiced
    correct_attempts = sum(1 for record in practice_records if safe_bool(getattr(record, 'is_correct', False)))
    accuracy = correct_attempts / total_attempts if total_attempts > 0 else 0
    
    total_time = sum(record.time_spent for record in practice_records)
    average_time = total_time / total_attempts if total_attempts > 0 else 0
    
    # 获取学科统计数据
    subject_stats = []
    subjects = db.query(Subject).all()
    for subj in subjects:
        subject_questions = db.query(Question).filter(
            and_(
                Question.user_id == current_user.id,
                Question.subject_id == subj.id
            )
        ).all()
        
        subject_total = len(subject_questions)
        if subject_total > 0:
            # 获取该学科的练习记录
            subject_practice_records = db.query(PracticeRecord).join(Question).filter(
                and_(
                    PracticeRecord.user_id == current_user.id,
                    Question.subject_id == subj.id
                )
            ).all()
            
            subject_correct = sum(1 for record in subject_practice_records if safe_bool(getattr(record, 'is_correct', False)))
            subject_total_time = sum(record.time_spent for record in subject_practice_records)
            
            subject_stats.append({
                "subject_id": subj.id,
                "subject_name": safe_str(getattr(subj, 'name', '')),
                "total": subject_total,
                "correct": subject_correct,
                "total_time": subject_total_time,
                "accuracy": subject_correct / len(subject_practice_records) if len(subject_practice_records) > 0 else 0
            })
    
    # 获取难度统计数据
    difficulty_stats = []
    for difficulty in ["easy", "medium", "hard"]:
        difficulty_questions = db.query(Question).filter(
            and_(
                Question.user_id == current_user.id,
                Question.difficulty == difficulty
            )
        ).all()
        
        difficulty_total = len(difficulty_questions)
        if difficulty_total > 0:
            # 获取该难度的练习记录
            difficulty_practice_records = db.query(PracticeRecord).join(Question).filter(
                and_(
                    PracticeRecord.user_id == current_user.id,
                    Question.difficulty == difficulty
                )
            ).all()
            
            difficulty_correct = sum(1 for record in difficulty_practice_records if safe_bool(getattr(record, 'is_correct', False)))
            difficulty_stats.append({
                "difficulty": difficulty,
                "count": difficulty_total,
                "correct": difficulty_correct,
                "accuracy": difficulty_correct / len(difficulty_practice_records) if len(difficulty_practice_records) > 0 else 0
            })
    
    # 获取每日统计数据（简化版）
    daily_stats = []
    # 在实际项目中，这里需要根据时间范围进行更复杂的查询
    
    # 获取每周统计数据（简化版）
    weekly_stats = []
    # 在实际项目中，这里需要根据时间范围进行更复杂的查询
    
    # 获取每月统计数据（简化版）
    monthly_stats = []
    # 在实际项目中，这里需要根据时间范围进行更复杂的查询
    
    return SuccessResponse(data={
        "basic_stats": {
            "total_questions": total_questions,
            "total_practiced": total_practiced,
            "total_attempts": total_attempts,
            "correct_attempts": correct_attempts,
            "accuracy": accuracy,
            "total_time": total_time,
            "average_time": average_time
        },
        "subject_stats": subject_stats,
        "difficulty_stats": difficulty_stats,
        "daily_stats": daily_stats,
        "weekly_stats": weekly_stats,
        "monthly_stats": monthly_stats
    })