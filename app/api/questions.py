from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.question import QuestionCreate, QuestionUpdate
from app.schemas.response import SuccessResponse
from app.services.question_service import QuestionService
from typing import cast
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
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
    try:
        logger.info(f"用户 {current_user.id} 请求题目列表")
        service = QuestionService(db)
        result = service.get_questions(
            user_id=cast(int, current_user.id),
            page=page,
            page_size=page_size,
            keyword=keyword,
            subject=subject,
            difficulty=difficulty,
            is_favorite=is_favorite,
            tags=tags,
            start_date=start_date,
            end_date=end_date,
            practice_status=practice_status
        )
        return SuccessResponse(data=result["data"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取题目列表时发生未预期的错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )

@router.get("/{question_id}")
def get_question(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"用户 {current_user.id} 请求题目详情: {question_id}")
        service = QuestionService(db)
        result = service.get_question_detail(user_id=cast(int, current_user.id), question_id=question_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="题目不存在"
            )
        
        return SuccessResponse(data=result["data"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取题目详情时发生未预期的错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_question(
    question: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"用户 {current_user.id} 创建题目")
        service = QuestionService(db)
        result = service.create_question(user_id=cast(int, current_user.id), question_data=question)
        return SuccessResponse(data=result["data"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建题目时发生未预期的错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )

@router.put("/{question_id}")
def update_question(
    question_id: int,
    question_update: QuestionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"用户 {current_user.id} 更新题目: {question_id}")
        service = QuestionService(db)
        result = service.update_question(
            user_id=cast(int, current_user.id),
            question_id=question_id,
            question_update=question_update
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="题目不存在"
            )
        
        return SuccessResponse(data=result["data"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新题目时发生未预期的错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )

@router.delete("/{question_id}")
def delete_question(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"用户 {current_user.id} 删除题目: {question_id}")
        service = QuestionService(db)
        success = service.delete_question(user_id=cast(int, current_user.id), question_id=question_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="题目不存在"
            )
        
        return SuccessResponse(data={
            "success": True,
            "message": "题目删除成功"
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除题目时发生未预期的错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )

@router.post("/{question_id}/toggle-favorite")
def toggle_favorite(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"用户 {current_user.id} 切换题目收藏状态: {question_id}")
        service = QuestionService(db)
        result = service.toggle_favorite(user_id=cast(int, current_user.id), question_id=question_id)
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="题目不存在"
            )
        
        return SuccessResponse(data={
            "isFavorite": result
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换题目收藏状态时发生未预期的错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )