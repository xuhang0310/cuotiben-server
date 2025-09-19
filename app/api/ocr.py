from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
import requests
import os
import uuid
from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.question import Question
from app.schemas.response import SuccessResponse
from app.utils.ocr import paddle_ocr_recognize

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
    recognized_text = paddle_ocr_recognize(image_data)
    
    return SuccessResponse(data={
        "recognizedText": recognized_text
    })

@router.post("/recognize-from-url")
async def ocr_recognize_from_url(
    image_url: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 验证URL格式
    if not image_url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=400,
            detail="请提供有效的图片URL"
        )
    
    # 初始化临时文件路径变量
    temp_filepath = None
    
    try:
        # 下载网络图片
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # 检查内容类型
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="URL指向的不是有效的图片文件"
            )
        
        # 生成临时文件路径
        temp_filename = f"temp_{uuid.uuid4().hex}.jpg"
        temp_filepath = os.path.join("/tmp", temp_filename)
        
        # 保存图片到临时文件
        with open(temp_filepath, "wb") as f:
            f.write(response.content)
        
        # 读取图片数据
        image_data = response.content
        
        # 调用OCR识别函数
        recognized_text = paddle_ocr_recognize(image_data)
        
        return SuccessResponse(data={
            "recognizedText": recognized_text
        })
        
    except requests.RequestException as e:
        raise HTTPException(
            status_code=400,
            detail=f"下载图片失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OCR识别过程中发生错误: {str(e)}"
        )
    finally:
        # 确保删除临时文件
        if temp_filepath and os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except:
                pass  # 忽略删除文件时的错误

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
    
    return SuccessResponse(data={
        "question": {
            "id": db_question.id,
            "title": db_question.title,
            "content": db_question.content,
            "options": [],
            "correctAnswer": db_question.correct_answer,
            "explanation": db_question.explanation,
            "difficulty": db_question.difficulty,
            "subject": "",  # 需要根据subject_id获取学科名称
            "tags": [],
            "isFavorite": db_question.is_favorite,
            "createdAt": db_question.created_at,
            "updatedAt": db_question.updated_at,
            "practiceCount": 0,
            "correctCount": 0,
            "lastPracticeAt": None
        }
    })