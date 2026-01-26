from sqlalchemy.orm import Session
from app.models.historical_figure import HistoricalFigure
from app.schemas.historical_figure import HistoricalFigureCreate, HistoricalFigureUpdate


def get_historical_figure(db: Session, figure_id: int):
    """根据ID获取历史人物"""
    return db.query(HistoricalFigure).filter(HistoricalFigure.id == figure_id).first()


def get_historical_figures(db: Session, skip: int = 0, limit: int = 10):
    """获取历史人物列表（支持分页）"""
    query = db.query(HistoricalFigure)
    total = query.count()
    figures = query.offset(skip).limit(limit).all()
    return figures, total


def create_historical_figure(db: Session, figure: HistoricalFigureCreate):
    """创建新的历史人物"""
    db_figure = HistoricalFigure(**figure.model_dump())
    db.add(db_figure)
    db.commit()
    db.refresh(db_figure)
    return db_figure


def update_historical_figure(db: Session, figure_id: int, figure_update: HistoricalFigureUpdate):
    """更新历史人物信息"""
    db_figure = db.query(HistoricalFigure).filter(HistoricalFigure.id == figure_id).first()
    if db_figure:
        update_data = figure_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_figure, field, value)
        db.commit()
        db.refresh(db_figure)
    return db_figure


def delete_historical_figure(db: Session, figure_id: int):
    """删除历史人物"""
    db_figure = db.query(HistoricalFigure).filter(HistoricalFigure.id == figure_id).first()
    if db_figure:
        db.delete(db_figure)
        db.commit()
    return db_figure