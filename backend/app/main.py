from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.router import api_router
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.services.seed import seed_if_empty

# create_all 不会给已有表补列，这里为旧库补齐高峰窗字段
_PEAK_COLUMNS = {
    "peak_start_min": "INTEGER",
    "peak_end_min": "INTEGER",
    "peak_headway_min": "DOUBLE PRECISION",
}


def _ensure_peak_columns() -> None:
    with engine.begin() as conn:
        for name, ddl in _PEAK_COLUMNS.items():
            conn.execute(text(f"ALTER TABLE lines ADD COLUMN IF NOT EXISTS {name} {ddl}"))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _ensure_peak_columns()
    if settings.seed_on_empty:
        db = SessionLocal()
        try:
            seed_if_empty(db)
        finally:
            db.close()
    yield


app = FastAPI(title="BusGap", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")
