from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Line
router = APIRouter(prefix="/lines", tags=["lines"])

def line_dict(r: Line) -> dict:
    return {"id": r.id, "code": r.code, "name": r.name, "planned_headway_min": r.planned_headway_min,
            "bunch_threshold": r.bunch_threshold, "large_threshold": r.large_threshold,
            "peak_start_min": r.peak_start_min, "peak_end_min": r.peak_end_min,
            "peak_headway_min": r.peak_headway_min}

@router.get("")
def list_lines(db: Session = Depends(get_db)):
    rows = db.scalars(select(Line).order_by(Line.id)).all()
    return [line_dict(r) for r in rows]

class PeakConfig(BaseModel):
    peak_start_min: int | None = None
    peak_end_min: int | None = None
    peak_headway_min: float | None = None

@router.put("/{line_id}/peak")
def update_peak(line_id: int, body: PeakConfig, db: Session = Depends(get_db)):
    line = db.get(Line, line_id)
    if not line:
        raise HTTPException(404, "线路不存在")
    values = (body.peak_start_min, body.peak_end_min, body.peak_headway_min)
    if all(v is None for v in values):
        # 全部留空 = 清除高峰配置，回到仅平峰计划间隔的行为
        line.peak_start_min = line.peak_end_min = line.peak_headway_min = None
    elif any(v is None for v in values):
        raise HTTPException(422, "高峰起止分钟与高峰间隔需同时提供；全部留空表示清除高峰配置")
    else:
        if not 0 <= body.peak_start_min < body.peak_end_min <= 1440:
            raise HTTPException(422, "高峰窗口需满足 0 ≤ 开始分钟 < 结束分钟 ≤ 1440")
        if body.peak_headway_min <= 0:
            raise HTTPException(422, "高峰计划间隔需大于 0")
        line.peak_start_min = body.peak_start_min
        line.peak_end_min = body.peak_end_min
        line.peak_headway_min = body.peak_headway_min
    db.commit()
    db.refresh(line)
    return line_dict(line)
