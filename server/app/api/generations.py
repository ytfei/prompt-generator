import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select
from sqlalchemy import text as sa_text

from app.agent.graph import stream_generation
from app.agent.refine import stream_refine
from app.db.models import Feedback, Generation, new_id, now_iso
from app.db.session import SessionLocal
from app.schemas import FeedbackCreate, GenerationCreate, GenerationOut, RefineCreate

router = APIRouter(prefix="/api/generations", tags=["generations"])


def to_out(row: Generation, rating: int | None = None) -> GenerationOut:
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
        parent_id=row.parent_id,
        rating=rating,
    )


async def get_row(gen_id: str) -> Generation:
    async with SessionLocal() as session:
        row = await session.get(Generation, gen_id)
    if not row:
        raise HTTPException(status_code=404, detail="generation not found")
    return row


async def ratings_for(gen_ids: list[str]) -> dict[str, int]:
    """批量取每条生成的最新反馈评分。"""
    if not gen_ids:
        return {}
    async with SessionLocal() as session:
        rows = (await session.execute(
            select(Feedback)
            .where(Feedback.generation_id.in_(gen_ids))
            .order_by(Feedback.created_at)
        )).scalars().all()
    return {r.generation_id: r.rating for r in rows}  # 后写覆盖先写 = 最新


@router.post("")
async def create_generation(body: GenerationCreate):
    """创建生成，响应为 SSE 流（step/warn/result/error 事件）。"""
    return StreamingResponse(
        stream_generation(body.selections, body.theme, body.mode, body.model_tier),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{gen_id}/refine")
async def refine_generation(gen_id: str, body: RefineCreate):
    """基于某条生成结果按指令继续修改，响应为 SSE 流；产出新行（mode=refine）。"""
    row = await get_row(gen_id)
    return StreamingResponse(
        stream_refine(
            gen_id, row.final_prompt, json.loads(row.selections), body.instruction, body.model_tier
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{gen_id}/feedback")
async def submit_feedback(gen_id: str, body: FeedbackCreate):
    """记录出图反馈（覆盖式：每次提交替换旧评价）。"""
    if body.rating not in (1, -1):
        raise HTTPException(status_code=422, detail="rating must be 1 or -1")
    await get_row(gen_id)
    async with SessionLocal() as session:
        await session.execute(
            sa_text("DELETE FROM feedback WHERE generation_id = :gid"),
            {"gid": gen_id},
        )
        session.add(Feedback(
            id=new_id(), generation_id=gen_id,
            rating=body.rating, comment=body.comment, created_at=now_iso(),
        ))
        await session.commit()
    return {"ok": True, "rating": body.rating}


@router.get("")
async def list_generations(limit: int = 50, offset: int = 0, favorite: bool | None = None):
    async with SessionLocal() as session:
        q = select(Generation).order_by(desc(Generation.created_at)).limit(limit).offset(offset)
        if favorite is not None:
            q = q.where(Generation.favorite == int(favorite))
        rows = (await session.execute(q)).scalars().all()
    ratings = await ratings_for([r.id for r in rows])
    return [to_out(r, ratings.get(r.id)) for r in rows]


@router.get("/{gen_id}")
async def get_generation(gen_id: str):
    row = await get_row(gen_id)
    ratings = await ratings_for([gen_id])
    return to_out(row, ratings.get(gen_id))


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
