from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.models import Base

engine = create_async_engine(settings.database_url)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    """建表（含 data 目录）。单用户本地工具，M5 前用 create_all，不引 Alembic。"""
    if settings.database_url.startswith("sqlite"):
        db_path = settings.database_url.split("///")[-1]
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # 旧库兼容：generations 表补 parent_id 列（新库由 create_all 直接建出）
        res = await conn.execute(text("PRAGMA table_info(generations)"))
        cols = {r[1] for r in res}
        if "parent_id" not in cols:
            await conn.execute(text("ALTER TABLE generations ADD COLUMN parent_id TEXT"))
