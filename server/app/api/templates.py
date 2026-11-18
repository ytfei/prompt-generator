import json

from fastapi import APIRouter, HTTPException
from sqlalchemy import desc, select

from app.db.models import Template, new_id, now_iso
from app.db.session import SessionLocal
from app.schemas import TemplateCreate, TemplateOut

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("")
async def list_templates() -> list[TemplateOut]:
    async with SessionLocal() as session:
        rows = (await session.execute(
            select(Template).order_by(desc(Template.created_at))
        )).scalars().all()
    return [
        TemplateOut(
            id=r.id, name=r.name,
            selections=json.loads(r.selections), created_at=r.created_at,
        )
        for r in rows
    ]


@router.post("")
async def create_template(body: TemplateCreate) -> TemplateOut:
    row = Template(
        id=new_id(), name=body.name,
        selections=json.dumps(body.selections, ensure_ascii=False), created_at=now_iso(),
    )
    async with SessionLocal() as session:
        session.add(row)
        await session.commit()
    return TemplateOut(
        id=row.id, name=row.name,
        selections=json.loads(row.selections), created_at=row.created_at,
    )


@router.delete("/{tpl_id}")
async def delete_template(tpl_id: str):
    async with SessionLocal() as session:
        row = await session.get(Template, tpl_id)
        if not row:
            raise HTTPException(status_code=404, detail="template not found")
        await session.delete(row)
        await session.commit()
    return {"ok": True}
