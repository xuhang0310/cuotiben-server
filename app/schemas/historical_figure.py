from pydantic import BaseModel
from typing import Optional, List


class HistoricalFigureBase(BaseModel):
    name: str
    avatar: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = "offline"
    create_time: Optional[str] = None


class HistoricalFigureCreate(HistoricalFigureBase):
    pass


class HistoricalFigureUpdate(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    create_time: Optional[str] = None


class HistoricalFigureResponse(HistoricalFigureBase):
    id: int

    model_config = {"from_attributes": True}


class PaginatedHistoricalFigures(BaseModel):
    total: int
    page: int
    size: int
    pages: int
    data: List[HistoricalFigureResponse]