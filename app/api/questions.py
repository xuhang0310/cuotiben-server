from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.question import Question
from app.models.subject import Subject
from app.models.question_option import QuestionOption
from app.models.tag import Tag
from app.models.question_tag import QuestionTag
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionListResponse, QuestionDetailResponse, FavoriteToggleResponse

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

@router.get("/", response_model=QuestionListResponse)
def get_questions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    subject: Optional[str] = None,
    difficulty: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    tags: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    practice_status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 构建查询
    query = db.query(Question).filter(Question.user_id == current_user.id)
    
    # 添加各种筛选条件
    if keyword:
        query = query.filter(
            or_(
                Question.title.like(f"%{keyword}%"),
                Question.content.like(f"%{keyword}%")
            )
        )
    
    if subject:
        subject_obj = db.query(Subject).filter(Subject.name == subject).first()
        if subject_obj:
            query = query.filter(Question.subject_id == subject_obj.id)
    
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    
    if is_favorite is not None:
        query = query.filter(Question.is_favorite == is_favorite)
    
    # 获取总记录数
    total = query.count()
    
    # 添加分页
    offset = (page - 1) * page_size
    questions = query.order_by(Question.created_at.desc()).offset(offset).limit(page_size).all()
    
    # 转换为响应格式
    question_list = []
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
        
        # 简化的练习统计数据（实际项目中需要更复杂的查询）
        practice_count = 0
        correct_count = 0
        last_practice_at = None
        
        question_list.append({
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
        "questions": question_list,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{question_id}", response_model=QuestionDetailResponse)
def get_question(
    question_id: int,
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
    
    question_data = {
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
    }
    
    # 获取相关题目（基于相同学科）
    related_questions = db.query(Question).filter(
        and_(
            Question.subject_id == question.subject_id,
            Question.id != question_id
        )
    ).limit(5).all()
    
    related_question_list = []
    for related_question in related_questions:
        # 获取相关题目的学科名称
        related_subject_obj = db.query(Subject).filter(Subject.id == related_question.subject_id).first()
        related_subject_name = safe_str(getattr(related_subject_obj, 'name', '')) if related_subject_obj else ""
        
        # 简化的练习统计数据
        related_practice_count = 0
        related_correct_count = 0
        related_last_practice_at = None
        
        # 获取相关题目的选项
        related_options = db.query(QuestionOption).filter(QuestionOption.question_id == related_question.id).all()
        related_option_texts = [safe_str(option.option_text) for option in related_options]
        
        # 获取相关题目的标签
        related_question_tags = db.query(QuestionTag).filter(QuestionTag.question_id == related_question.id).all()
        related_tag_ids = [qt.tag_id for qt in related_question_tags]
        related_tag_names = []
        if related_tag_ids:
            related_tag_objects = db.query(Tag).filter(Tag.id.in_(related_tag_ids)).all()
            related_tag_names = [safe_str(getattr(tag, 'name', '')) for tag in related_tag_objects]
        
        related_question_list.append({
            "id": related_question.id,
            "title": safe_str(getattr(related_question, 'title', '')),
            "content": safe_str(getattr(related_question, 'content', '')),
            "options": related_option_texts,
            "correct_answer": safe_str(getattr(related_question, 'correct_answer', None)),
            "explanation": safe_str(getattr(related_question, 'explanation', None)),
            "difficulty": safe_str(getattr(related_question, 'difficulty', '')),
            "subject": related_subject_name,
            "tags": related_tag_names,
            "is_favorite": safe_bool(getattr(related_question, 'is_favorite', False)),
            "created_at": getattr(related_question, 'created_at', None),
            "updated_at": getattr(related_question, 'updated_at', None),
            "practice_count": related_practice_count,
            "correct_count": related_correct_count,
            "last_practice_at": related_last_practice_at
        })
    
    return {
        "question": question_data,
        "related_questions": related_question_list
    }

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_question(
    question: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 创建题目
    db_question = Question(
        user_id=current_user.id,
        title=question.title,
        content=question.content,
        question_type_id=question.question_type_id,
        difficulty=question.difficulty,
        subject_id=question.subject_id,
        explanation=question.explanation,
        correct_answer=question.correct_answer,
        image_url=question.image_url,
        is_favorite=False
    )
    
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    
    # 获取学科名称
    subject_obj = db.query(Subject).filter(Subject.id == db_question.subject_id).first()
    subject_name = safe_str(getattr(subject_obj, 'name', '')) if subject_obj else ""
    
    return {
        "success": True,
        "data": {
            "question": {
                "id": db_question.id,
                "title": safe_str(getattr(db_question, 'title', '')),
                "content": safe_str(getattr(db_question, 'content', '')),
                "options": [],
                "correct_answer": safe_str(getattr(db_question, 'correct_answer', None)),
                "explanation": safe_str(getattr(db_question, 'explanation', None)),
                "difficulty": safe_str(getattr(db_question, 'difficulty', '')),
                "subject": subject_name,
                "tags": [],
                "is_favorite": safe_bool(getattr(db_question, 'is_favorite', False)),
                "created_at": getattr(db_question, 'created_at', None),
                "updated_at": getattr(db_question, 'updated_at', None),
                "practice_count": 0,
                "correct_count": 0,
                "last_practice_at": None
            }
        }
    }

@router.put("/{question_id}")
def update_question(
    question_id: int,
    question_update: QuestionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 获取题目
    db_question = db.query(Question).filter(
        and_(
            Question.id == question_id,
            Question.user_id == current_user.id
        )
    ).first()
    
    if not db_question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )
    
    # 更新题目信息
    update_data = question_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(db_question, field):
            setattr(db_question, field, value)
    
    db.commit()
    db.refresh(db_question)
    
    # 获取选项
    options = db.query(QuestionOption).filter(QuestionOption.question_id == db_question.id).all()
    option_texts = [safe_str(option.option_text) for option in options]
    
    # 获取标签
    question_tags = db.query(QuestionTag).filter(QuestionTag.question_id == db_question.id).all()
    tag_ids = [qt.tag_id for qt in question_tags]
    tag_names = []
    if tag_ids:
        tag_objects = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        tag_names = [safe_str(getattr(tag, 'name', '')) for tag in tag_objects]
    
    # 获取学科名称
    subject_obj = db.query(Subject).filter(Subject.id == db_question.subject_id).first()
    subject_name = safe_str(getattr(subject_obj, 'name', '')) if subject_obj else ""
    
    # 简化的练习统计数据
    practice_count = 0
    correct_count = 0
    last_practice_at = None
    
    return {
        "success": True,
        "data": {
            "question": {
                "id": db_question.id,
                "title": safe_str(getattr(db_question, 'title', '')),
                "content": safe_str(getattr(db_question, 'content', '')),
                "options": option_texts,
                "correct_answer": safe_str(getattr(db_question, 'correct_answer', None)),
                "explanation": safe_str(getattr(db_question, 'explanation', None)),
                "difficulty": safe_str(getattr(db_question, 'difficulty', '')),
                "subject": subject_name,
                "tags": tag_names,
                "is_favorite": safe_bool(getattr(db_question, 'is_favorite', False)),
                "created_at": getattr(db_question, 'created_at', None),
                "updated_at": getattr(db_question, 'updated_at', None),
                "practice_count": practice_count,
                "correct_count": correct_count,
                "last_practice_at": last_practice_at
            }
        }
    }

@router.delete("/{question_id}")
def delete_question(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 获取题目
    db_question = db.query(Question).filter(
        and_(
            Question.id == question_id,
            Question.user_id == current_user.id
        )
    ).first()
    
    if not db_question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )
    
    db.delete(db_question)
    db.commit()
    
    return {
        "success": True,
        "message": "题目删除成功"
    }

@router.post("/{question_id}/toggle-favorite", response_model=FavoriteToggleResponse)
def toggle_favorite(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 获取题目
    db_question = db.query(Question).filter(
        and_(
            Question.id == question_id,
            Question.user_id == current_user.id
        )
    ).first()
    
    if not db_question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )
    
    # 切换收藏状态
    current_favorite = safe_bool(getattr(db_question, 'is_favorite', False))
    setattr(db_question, 'is_favorite', not current_favorite)
    db.commit()
    db.refresh(db_question)
    
    return {
        "is_favorite": safe_bool(getattr(db_question, 'is_favorite', False))
    }