from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from app.models.question import Question
from app.models.subject import Subject
from app.models.question_option import QuestionOption
from app.models.tag import Tag
from app.models.question_tag import QuestionTag
from app.schemas.question import QuestionCreate, QuestionUpdate
from app.models.user import User
import logging
from typing import cast
from app.utils.question_utils import safe_str, safe_bool, safe_int, safe_datetime
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class QuestionService:
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)

    def get_questions(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        keyword: Optional[str] = None,
        subject: Optional[str] = None,
        difficulty: Optional[str] = None,
        is_favorite: Optional[bool] = None,
        tags: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        practice_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取题目列表"""
        try:
            self.logger.info(f"获取题目列表: user_id={user_id}, page={page}, page_size={page_size}")
            
            # 构建查询
            query = self.db.query(Question).filter(Question.user_id == user_id)
            
            # 添加各种筛选条件
            if keyword:
                query = query.filter(
                    or_(
                        Question.title.like(f"%{keyword}%"),
                        Question.content.like(f"%{keyword}%")
                    )
                )
            
            if subject:
                subject_obj = self.db.query(Subject).filter(Subject.name == subject).first()
                if subject_obj:
                    query = query.filter(Question.subject_id == subject_obj.id)
            
            if difficulty:
                query = query.filter(Question.difficulty == difficulty)
            
            if is_favorite is not None:
                query = query.filter(Question.is_favorite == is_favorite)
                
            # 实现practice_status筛选
            if practice_status:
                # 这里需要根据练习记录来筛选题目
                # 由于练习记录表未提供详细结构，暂时留空
                pass
            
            # 实现tags筛选
            if tags:
                tag_list = tags.split(',')
                tag_objects = self.db.query(Tag).filter(Tag.name.in_(tag_list)).all()
                tag_ids = [tag.id for tag in tag_objects]
                if tag_ids:
                    # 查询包含这些标签的题目
                    question_ids_with_tags = self.db.query(QuestionTag.question_id).filter(
                        QuestionTag.tag_id.in_(tag_ids)
                    ).distinct().all()
                    question_ids_list = [q.question_id for q in question_ids_with_tags]
                    query = query.filter(Question.id.in_(question_ids_list))
            
            # 实现时间范围筛选
            if start_date:
                query = query.filter(Question.created_at >= start_date)
            if end_date:
                query = query.filter(Question.created_at <= end_date)
            
            # 获取总记录数
            total = query.count()
            
            # 添加分页
            offset = (page - 1) * page_size
            questions = query.order_by(Question.created_at.desc()).offset(offset).limit(page_size).all()
            
            # 批量获取关联数据
            question_ids = [cast(int, q.id) for q in questions]
            options_map = self._get_options_map(question_ids)
            tags_map = self._get_tags_map(question_ids)
            subjects_map = self._get_subjects_map([cast(int, q.subject_id) for q in questions])
            
            # 转换为响应格式
            question_list = []
            for question in questions:
                # 获取选项
                option_texts = options_map.get(cast(int, question.id), [])
                
                # 获取标签
                tag_names = tags_map.get(cast(int, question.id), [])
                
                # 获取学科名称
                subject_name = subjects_map.get(cast(int, question.subject_id), "")
                
                # 简化的练习统计数据（实际项目中需要更复杂的查询）
                practice_count = 0
                correct_count = 0
                last_practice_at = None
                
                question_list.append({
                    "id": safe_int(question.id),
                    "user_id": safe_int(question.user_id),
                    "title": safe_str(question.title),
                    "content": safe_str(question.content),
                    "question_type_id": safe_int(question.question_type_id),
                    "options": option_texts,
                    "correct_answer": safe_str(question.correct_answer),
                    "explanation": safe_str(question.explanation),
                    "difficulty": safe_str(question.difficulty),
                    "subject_id": safe_int(question.subject_id),
                    "subject": subject_name,
                    "tags": tag_names,
                    "is_favorite": safe_bool(question.is_favorite),
                    "created_at": safe_datetime(question.created_at),
                    "updated_at": safe_datetime(question.updated_at),
                    "practice_count": practice_count,
                    "correct_count": correct_count,
                    "last_practice_at": last_practice_at
                })
            
            self.logger.info(f"成功获取题目列表: total={total}")
            return {
                "data": {
                    "questions": question_list,
                    "total": total,
                    "page": page,
                    "pageSize": page_size
                }
            }
        except Exception as e:
            self.logger.error(f"获取题目列表时发生错误: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取题目列表失败"
            )

    def get_question_detail(self, user_id: int, question_id: int) -> Optional[Dict[str, Any]]:
        """获取题目详情"""
        try:
            self.logger.info(f"获取题目详情: user_id={user_id}, question_id={question_id}")
            
            # 获取题目
            question = self.db.query(Question).filter(
                and_(
                    Question.id == question_id,
                    Question.user_id == user_id
                )
            ).first()
            
            if not question:
                self.logger.warning(f"题目不存在: user_id={user_id}, question_id={question_id}")
                return None
            
            # 获取选项
            options = self.db.query(QuestionOption).filter(QuestionOption.question_id == question.id).all()
            option_texts = [cast(str, option.option_text) for option in options]
            
            # 获取标签
            question_tags = self.db.query(QuestionTag).filter(QuestionTag.question_id == question.id).all()
            tag_ids = [qt.tag_id for qt in question_tags]
            tag_names = []
            if tag_ids:
                tag_objects = self.db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
                tag_names = [cast(str, tag.name) for tag in tag_objects]
            
            # 获取学科名称
            subject_obj = self.db.query(Subject).filter(Subject.id == question.subject_id).first()
            subject_name = cast(str, subject_obj.name) if subject_obj else ""
            
            # 简化的练习统计数据
            practice_count = 0
            correct_count = 0
            last_practice_at = None
            
            question_data = {
                "id": safe_int(question.id),
                "user_id": safe_int(question.user_id),
                "title": safe_str(question.title),
                "content": safe_str(question.content),
                "question_type_id": safe_int(question.question_type_id),
                "options": option_texts,
                "correct_answer": safe_str(question.correct_answer),
                "explanation": safe_str(question.explanation),
                "difficulty": safe_str(question.difficulty),
                "subject_id": safe_int(question.subject_id),
                "subject": subject_name,
                "tags": tag_names,
                "is_favorite": safe_bool(question.is_favorite),
                "created_at": safe_datetime(question.created_at),
                "updated_at": safe_datetime(question.updated_at),
                "practice_count": practice_count,
                "correct_count": correct_count,
                "last_practice_at": last_practice_at
            }
            
            # 获取相关题目（基于相同学科）
            related_questions = self.db.query(Question).filter(
                and_(
                    Question.subject_id == question.subject_id,
                    Question.id != question_id
                )
            ).limit(5).all()
            
            # 批量获取相关题目的关联数据
            related_question_ids = [cast(int, q.id) for q in related_questions]
            related_options_map = self._get_options_map(related_question_ids) if related_question_ids else {}
            related_tags_map = self._get_tags_map(related_question_ids) if related_question_ids else {}
            related_subject_ids = [cast(int, q.subject_id) for q in related_questions]
            related_subjects_map = self._get_subjects_map(related_subject_ids) if related_subject_ids else {}
            
            related_question_list = []
            for related_question in related_questions:
                # 获取相关题目的选项
                related_option_texts = related_options_map.get(cast(int, related_question.id), [])
                
                # 获取相关题目的标签
                related_tag_names = related_tags_map.get(cast(int, related_question.id), [])
                
                # 获取相关题目的学科名称
                related_subject_name = related_subjects_map.get(cast(int, related_question.subject_id), "")
                
                # 简化的练习统计数据
                related_practice_count = 0
                related_correct_count = 0
                related_last_practice_at = None
                
                related_question_list.append({
                    "id": safe_int(related_question.id),
                    "user_id": safe_int(related_question.user_id),
                    "title": safe_str(related_question.title),
                    "content": safe_str(related_question.content),
                    "question_type_id": safe_int(related_question.question_type_id),
                    "options": related_option_texts,
                    "correct_answer": safe_str(related_question.correct_answer),
                    "explanation": safe_str(related_question.explanation),
                    "difficulty": safe_str(related_question.difficulty),
                    "subject_id": safe_int(related_question.subject_id),
                    "subject": related_subject_name,
                    "tags": related_tag_names,
                    "is_favorite": safe_bool(related_question.is_favorite),
                    "created_at": safe_datetime(related_question.created_at),
                    "updated_at": safe_datetime(related_question.updated_at),
                    "practice_count": related_practice_count,
                    "correct_count": related_correct_count,
                    "last_practice_at": related_last_practice_at
                })
            
            self.logger.info(f"成功获取题目详情: question_id={question_id}")
            return {
                "data": {
                    "question": question_data,
                    "related_questions": related_question_list
                }
            }
        except Exception as e:
            self.logger.error(f"获取题目详情时发生错误: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取题目详情失败"
            )

    def create_question(self, user_id: int, question_data: QuestionCreate) -> Dict[str, Any]:
        """创建题目"""
        try:
            self.logger.info(f"创建题目: user_id={user_id}")
            
            # 创建题目
            db_question = Question(
                user_id=user_id,
                title=question_data.title,
                content=question_data.content,
                question_type_id=question_data.question_type_id,
                difficulty=question_data.difficulty,
                subject_id=question_data.subject_id,
                explanation=question_data.explanation,
                correct_answer=question_data.correct_answer,
                image_url=question_data.image_url,
                is_favorite=False
            )
            
            self.db.add(db_question)
            self.db.commit()
            self.db.refresh(db_question)
            
            # 获取学科名称
            subject_obj = self.db.query(Subject).filter(Subject.id == db_question.subject_id).first()
            subject_name = cast(str, subject_obj.name) if subject_obj else ""
            
            self.logger.info(f"成功创建题目: question_id={db_question.id}")
            return {
                "data": {
                    "question": {
                        "id": safe_int(db_question.id),
                        "user_id": safe_int(db_question.user_id),
                        "title": safe_str(db_question.title),
                        "content": safe_str(db_question.content),
                        "question_type_id": safe_int(db_question.question_type_id),
                        "options": [],
                        "correct_answer": safe_str(db_question.correct_answer),
                        "explanation": safe_str(db_question.explanation),
                        "difficulty": safe_str(db_question.difficulty),
                        "subject_id": safe_int(db_question.subject_id),
                        "subject": subject_name,
                        "tags": [],
                        "is_favorite": safe_bool(db_question.is_favorite),
                        "created_at": safe_datetime(db_question.created_at),
                        "updated_at": safe_datetime(db_question.updated_at),
                        "practice_count": 0,
                        "correct_count": 0,
                        "last_practice_at": None
                    }
                }
            }
        except Exception as e:
            self.logger.error(f"创建题目时发生错误: {str(e)}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建题目失败"
            )

    def update_question(self, user_id: int, question_id: int, question_update: QuestionUpdate) -> Optional[Dict[str, Any]]:
        """更新题目"""
        try:
            self.logger.info(f"更新题目: user_id={user_id}, question_id={question_id}")
            
            # 获取题目
            db_question = self.db.query(Question).filter(
                and_(
                    Question.id == question_id,
                    Question.user_id == user_id
                )
            ).first()
            
            if not db_question:
                self.logger.warning(f"题目不存在: user_id={user_id}, question_id={question_id}")
                return None
            
            # 更新题目信息
            update_data = question_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(db_question, field):
                    setattr(db_question, field, value)
            
            self.db.commit()
            self.db.refresh(db_question)
            
            # 获取选项
            options = self.db.query(QuestionOption).filter(QuestionOption.question_id == db_question.id).all()
            option_texts = [cast(str, option.option_text) for option in options]
            
            # 获取标签
            question_tags = self.db.query(QuestionTag).filter(QuestionTag.question_id == db_question.id).all()
            tag_ids = [qt.tag_id for qt in question_tags]
            tag_names = []
            if tag_ids:
                tag_objects = self.db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
                tag_names = [cast(str, tag.name) for tag in tag_objects]
            
            # 获取学科名称
            subject_obj = self.db.query(Subject).filter(Subject.id == db_question.subject_id).first()
            subject_name = cast(str, subject_obj.name) if subject_obj else ""
            
            # 简化的练习统计数据
            practice_count = 0
            correct_count = 0
            last_practice_at = None
            
            self.logger.info(f"成功更新题目: question_id={question_id}")
            return {
                "data": {
                    "question": {
                        "id": safe_int(db_question.id),
                        "user_id": safe_int(db_question.user_id),
                        "title": safe_str(db_question.title),
                        "content": safe_str(db_question.content),
                        "question_type_id": safe_int(db_question.question_type_id),
                        "options": option_texts,
                        "correct_answer": safe_str(db_question.correct_answer),
                        "explanation": safe_str(db_question.explanation),
                        "difficulty": safe_str(db_question.difficulty),
                        "subject_id": safe_int(db_question.subject_id),
                        "subject": subject_name,
                        "tags": tag_names,
                        "is_favorite": safe_bool(db_question.is_favorite),
                        "created_at": safe_datetime(db_question.created_at),
                        "updated_at": safe_datetime(db_question.updated_at),
                        "practice_count": practice_count,
                        "correct_count": correct_count,
                        "last_practice_at": last_practice_at
                    }
                }
            }
        except Exception as e:
            self.logger.error(f"更新题目时发生错误: {str(e)}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新题目失败"
            )

    def delete_question(self, user_id: int, question_id: int) -> bool:
        """删除题目"""
        try:
            self.logger.info(f"删除题目: user_id={user_id}, question_id={question_id}")
            
            # 获取题目
            db_question = self.db.query(Question).filter(
                and_(
                    Question.id == question_id,
                    Question.user_id == user_id
                )
            ).first()
            
            if not db_question:
                self.logger.warning(f"题目不存在: user_id={user_id}, question_id={question_id}")
                return False
            
            self.db.delete(db_question)
            self.db.commit()
            
            self.logger.info(f"成功删除题目: question_id={question_id}")
            return True
        except Exception as e:
            self.logger.error(f"删除题目时发生错误: {str(e)}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除题目失败"
            )

    def toggle_favorite(self, user_id: int, question_id: int) -> Optional[bool]:
        """切换收藏状态"""
        try:
            self.logger.info(f"切换收藏状态: user_id={user_id}, question_id={question_id}")
            
            # 获取题目
            db_question = self.db.query(Question).filter(
                and_(
                    Question.id == question_id,
                    Question.user_id == user_id
                )
            ).first()
            
            if not db_question:
                self.logger.warning(f"题目不存在: user_id={user_id}, question_id={question_id}")
                return None
            
            # 切换收藏状态
            current_favorite = cast(bool, db_question.is_favorite)
            setattr(db_question, 'is_favorite', not current_favorite)
            self.db.commit()
            self.db.refresh(db_question)
            
            result = cast(bool, db_question.is_favorite)
            self.logger.info(f"成功切换收藏状态: question_id={question_id}, is_favorite={result}")
            return result
        except Exception as e:
            self.logger.error(f"切换收藏状态时发生错误: {str(e)}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="切换收藏状态失败"
            )

    def _get_options_map(self, question_ids: List[int]) -> Dict[int, List[str]]:
        """批量获取题目选项"""
        if not question_ids:
            return {}
        
        options = self.db.query(QuestionOption).filter(
            QuestionOption.question_id.in_(question_ids)
        ).all()
        
        options_map = {}
        for option in options:
            if option.question_id not in options_map:
                options_map[option.question_id] = []
            options_map[option.question_id].append(cast(str, option.option_text))
        
        return options_map

    def _get_tags_map(self, question_ids: List[int]) -> Dict[int, List[str]]:
        """批量获取题目标签"""
        if not question_ids:
            return {}
        
        # 查询题目标签关联
        question_tags = self.db.query(QuestionTag).filter(
            QuestionTag.question_id.in_(question_ids)
        ).all()
        
        # 获取标签ID
        tag_ids = [qt.tag_id for qt in question_tags]
        question_tag_map = {}
        for qt in question_tags:
            if qt.question_id not in question_tag_map:
                question_tag_map[qt.question_id] = []
            question_tag_map[qt.question_id].append(qt.tag_id)
        
        # 获取标签名称
        tag_names = {}
        if tag_ids:
            tags = self.db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
            tag_names = {tag.id: tag.name for tag in tags}
        
        # 构建题目ID到标签名称的映射
        tags_map = {}
        for question_id, tag_id_list in question_tag_map.items():
            tags_map[question_id] = [tag_names.get(tag_id, "") for tag_id in tag_id_list]
        
        return tags_map

    def _get_subjects_map(self, subject_ids: List[int]) -> Dict[int, str]:
        """批量获取学科信息"""
        if not subject_ids:
            return {}
        
        subjects = self.db.query(Subject).filter(Subject.id.in_(subject_ids)).all()
        return {cast(int, subject.id): cast(str, subject.name) for subject in subjects}