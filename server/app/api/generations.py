import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select

from app.agent.graph import stream_generation
from app.db.models import Generation
from app.db.session import SessionLocal
from app.schemas import GenerationCreate, GenerationOut

router = APIRouter(prefix="/api/generations", tags=["generations"])


def to_out(row: Generation) -> GenerationOut:
    return GenerationOut(
        id=row.id,
        created_at=row.created_at,
        selections=json.loads(row.selections),
        theme=row.theme,
        final_prompt=row.final_prompt,
        notes=json.loads(row.notes),
        warnings=json.loads(row.warnings),
        model=row.model,
        mode=row.mode,
        favorite=bool(row.favorite),
    )


async def get_row(gen_id: str) -> Generation:
    async with SessionLocal() as session:
        row = await session.get(Generation, gen_id)
    if not row:
        raise HTTPException(status_code=404, detail="generation not found")
    return row


@router.post("")
async def create_generation(body: GenerationCreate):
    """创建生成，响应为 SSE 流（step/warn/result/error 事件）。"""
    return StreamingResponse(
        stream_generation(body.selections, body.theme, body.mode),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("")
async def list_generations(limit: int = 50, offset: int = 0, favorite: bool | None = None):
    async with SessionLocal() as session:
        q = select(Generation).order_by(desc(Generation.created_at)).limit(limit).offset(offset)
        if favorite is not None:
            q = q.where(Generation.favorite == int(favorite))
        rows = (await session.execute(q)).scalars().all()
    return [to_out(r) for r in rows]


@router.get("/{gen_id}")
async def get_generation(gen_id: str):
    return to_out(await get_row(gen_id))


@router.patch("/{gen_id}")
async def update_generation(gen_id: str, body: dict):
    if "favorite" not in body:
        raise HTTPException(status_code=422, detail="favorite required")
    async with SessionLocal() as session:
        row = await session.get(Generation, gen_id)
        if not row:
            raise HTTPException(status_code=404, detail="generation not found")
        row.favorite = int(bool(body["favorite"]))
        await session.commit()
        return to_out(row)


@router.delete("/{gen_id}")
async def delete_generation(gen_id: str):
    await get_row(gen_id)
    async with SessionLocal() as session:
        row = await session.get(Generation, gen_id)
        await session.delete(row)
        await session.commit()
    return {"ok": True}
