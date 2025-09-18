from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.question import Question
from app.utils.ocr import mock_ocr_recognize

router = APIRouter()

@router.post("/recognize")
async def ocr_recognize(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查文件类型
    if image.content_type is None or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="请上传图片文件"
        )
    
    # 读取图片数据
    image_data = await image.read()
    
    # 调用OCR识别函数
    recognized_text = mock_ocr_recognize(image_data)
    
    return {
        "success": True,
        "data": {
            "recognized_text": recognized_text
        }
    }

@router.post("/save-question")
def save_ocr_question(
    title: str = Form(...),
    content: str = Form(...),
    question_type_id: int = Form(1),
    difficulty: str = Form("medium"),
    subject_id: int = Form(1),
    explanation: str = Form(None),
    correct_answer: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 创建题目
    db_question = Question(
        user_id=current_user.id,
        title=title,
        content=content,
        question_type_id=question_type_id,
        difficulty=difficulty,
        subject_id=subject_id,
        explanation=explanation,
        correct_answer=correct_answer,
        is_favorite=False
    )
    
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    
    return {
        "success": True,
        "data": {
            "question": {
                "id": db_question.id,
                "title": db_question.title,
                "content": db_question.content,
                "options": [],
                "correct_answer": db_question.correct_answer,
                "explanation": db_question.explanation,
                "difficulty": db_question.difficulty,
                "subject": "",  # 需要根据subject_id获取学科名称
                "tags": [],
                "is_favorite": db_question.is_favorite,
                "created_at": db_question.created_at,
                "updated_at": db_question.updated_at,
                "practice_count": 0,
                "correct_count": 0,
                "last_practice_at": None
            }
        }
    }