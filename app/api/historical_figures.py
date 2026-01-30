from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database.session import get_db
from app.schemas.historical_figure import (
    HistoricalFigureCreate,
    HistoricalFigureUpdate,
    HistoricalFigureResponse,
    PaginatedHistoricalFigures
)
from app.services.historical_figure import (
    get_historical_figure,
    get_historical_figures,
    create_historical_figure,
    update_historical_figure,
    delete_historical_figure
)

router = APIRouter(prefix="", tags=["historical-figures"])


@router.post("/", response_model=HistoricalFigureResponse)
def create_figure(figure: HistoricalFigureCreate, db: Session = Depends(get_db)):
    """创建新的历史人物"""
    return create_historical_figure(db=db, figure=figure)


@router.get("/{figure_id}", response_model=HistoricalFigureResponse)
def read_figure(figure_id: int, db: Session = Depends(get_db)):
    """根据ID获取历史人物"""
    db_figure = get_historical_figure(db=db, figure_id=figure_id)
    if db_figure is None:
        raise HTTPException(status_code=404, detail="历史人物不存在")
    return db_figure


@router.put("/{figure_id}", response_model=HistoricalFigureResponse)
def update_figure(
    figure_id: int, figure_update: HistoricalFigureUpdate, db: Session = Depends(get_db)
):
    """更新历史人物信息"""
    db_figure = update_historical_figure(db=db, figure_id=figure_id, figure_update=figure_update)
    if db_figure is None:
        raise HTTPException(status_code=404, detail="历史人物不存在")
    return db_figure


@router.delete("/{figure_id}")
def delete_figure(figure_id: int, db: Session = Depends(get_db)):
    """删除历史人物"""
    db_figure = delete_historical_figure(db=db, figure_id=figure_id)
    if db_figure is None:
        raise HTTPException(status_code=404, detail="历史人物不存在")
    return {"message": "历史人物删除成功"}


@router.get("/", response_model=PaginatedHistoricalFigures)
def read_figures(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="每页显示的记录数"),
    db: Session = Depends(get_db)
):
    """获取历史人物列表（支持分页）"""
    figures, total = get_historical_figures(db=db, skip=skip, limit=limit)

    # 处理头像URL - 如果不是以http开头，则拼接域名
    processed_figures = []
    for figure in figures:
        figure_dict = figure.__dict__.copy()  # 创建副本以避免修改原始对象
        if hasattr(figure, 'avatar') and figure.avatar:
            avatar = figure.avatar
            # 如果头像URL不是以http开头，则拼接域名
            if not avatar.lower().startswith(('http://', 'https://')):
                figure_dict['avatar'] = f"http://180.76.183.241/{avatar.lstrip('/')}"
        processed_figures.append(HistoricalFigureResponse(**figure_dict))

    # 计算总页数
    pages = (total + limit - 1) // limit

    return PaginatedHistoricalFigures(
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        pages=pages,
        data=processed_figures
    )