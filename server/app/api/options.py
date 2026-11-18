from fastapi import APIRouter

from app.agent.options_data import GROUPS, PRESETS

router = APIRouter(prefix="/api/options", tags=["options"])


@router.get("")
async def get_options():
    """下发 14 维度选项定义与内置预设（选项系统的唯一数据源）。"""
    return {"groups": GROUPS, "presets": PRESETS}
