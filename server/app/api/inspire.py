from fastapi import APIRouter

from app.agent.inspire import inspire_themes
from app.schemas import InspireCreate

router = APIRouter(prefix="/api", tags=["inspire"])


@router.post("/inspire-theme")
async def inspire(body: InspireCreate):
    """基于已选配置批量生成创意主题描述（启发灵感）。"""
    return {"themes": await inspire_themes(body.selections)}
