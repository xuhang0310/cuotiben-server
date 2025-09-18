from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional
from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.question import Question
from app.models.subject import Subject
from app.models.question_option import QuestionOption
from app.models.tag import Tag
from app.models.question_tag import QuestionTag
from app.models.practice_record import PracticeRecord

router = APIRouter()

def safe_str(value):
    """安全地将值转换为字符串"""
    if value is None:
        return None
    return str(value)

def safe_bool(value):
    """安全地将值转换为布尔值"""
    if value is None:
        return False
    return bool(value)

@router.post("/start")
def start_practice(
    mode: str = "all",
    count: int = 10,
    subject: Optional[str] = None,
    difficulty: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 构建查询
    query = db.query(Question).filter(Question.user_id == current_user.id)
    
    # 添加筛选条件
    if subject:
        subject_obj = db.query(Subject).filter(Subject.name == subject).first()
        if subject_obj:
            query = query.filter(Question.subject_id == subject_obj.id)
    
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    
    # 根据模式添加额外条件
    if mode == "favorite":
        query = query.filter(Question.is_favorite == True)
    elif mode == "wrong":
        # 在实际项目中，这里需要查询练习记录来找出错误的题目
        pass
    elif mode == "random":
        query = query.order_by(func.random())
    
    # 限制数量
    questions = query.limit(count).all()
    
    # 转换为响应格式
    practice_questions = []
    for question in questions:
        # 获取选项
        options = db.query(QuestionOption).filter(QuestionOption.question_id == question.id).all()
        option_texts = [safe_str(option.option_text) for option in options]
        
        # 获取标签
        question_tags = db.query(QuestionTag).filter(QuestionTag.question_id == question.id).all()
        tag_ids = [qt.tag_id for qt in question_tags]
        tag_names = []
        if tag_ids:
            tag_objects = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
            tag_names = [safe_str(getattr(tag, 'name', '')) for tag in tag_objects]
        
        # 获取学科名称
        subject_obj = db.query(Subject).filter(Subject.id == question.subject_id).first()
        subject_name = safe_str(getattr(subject_obj, 'name', '')) if subject_obj else ""
        
        # 简化的练习统计数据
        practice_count = 0
        correct_count = 0
        last_practice_at = None
        
        practice_questions.append({
            "id": question.id,
            "title": safe_str(getattr(question, 'title', '')),
            "content": safe_str(getattr(question, 'content', '')),
            "options": option_texts,
            "correct_answer": safe_str(getattr(question, 'correct_answer', None)),
            "explanation": safe_str(getattr(question, 'explanation', None)),
            "difficulty": safe_str(getattr(question, 'difficulty', '')),
            "subject": subject_name,
            "tags": tag_names,
            "is_favorite": safe_bool(getattr(question, 'is_favorite', False)),
            "created_at": getattr(question, 'created_at', None),
            "updated_at": getattr(question, 'updated_at', None),
            "practice_count": practice_count,
            "correct_count": correct_count,
            "last_practice_at": last_practice_at
        })
    
    return {
        "success": True,
        "data": {
            "practice_questions": practice_questions
        }
    }

@router.post("/submit")
def submit_answer(
    question_id: int,
    user_answer: str,
    time_spent: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 获取题目
    question = db.query(Question).filter(
        and_(
            Question.id == question_id,
            Question.user_id == current_user.id
        )
    ).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )
    
    # 简化的答案验证（实际项目中需要更复杂的逻辑）
    is_correct = user_answer == safe_str(getattr(question, 'correct_answer', ''))
    
    # 创建练习记录
    practice_record = PracticeRecord(
        user_id=current_user.id,
        question_id=question_id,
        user_answer=user_answer,
        correct_answer=safe_str(getattr(question, 'correct_answer', '')),
        is_correct=is_correct,
        time_spent=time_spent,
        record_type="practice"
    )
    
    db.add(practice_record)
    db.commit()
    db.refresh(practice_record)
    
    return {
        "success": True,
        "data": {
            "is_correct": is_correct,
            "correct_answer": safe_str(getattr(question, 'correct_answer', ''))
        }
    }

@router.get("/stats")
def get_practice_stats(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 获取练习记录
    practice_records = db.query(PracticeRecord).filter(
        PracticeRecord.user_id == current_user.id
    ).all()
    
    total_practice = len(practice_records)
    correct_count = sum(1 for record in practice_records if safe_bool(getattr(record, 'is_correct', False)))
    average_time = sum(record.time_spent for record in practice_records) / total_practice if total_practice > 0 else 0
    
    return {
        "success": True,
        "data": {
            "total_practice": total_practice,
            "correct_count": correct_count,
            "average_time": average_time
        }
    }