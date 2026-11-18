from fastapi import APIRouter

from app.agent.options_data import GROUPS, PRESETS
from app.core.config import settings

router = APIRouter(prefix="/api/options", tags=["options"])

TIER_LABELS = {"default": "默认", "nano": "⚡ 快", "mid": "⚖ 中", "pro": "🧠 强"}


@router.get("")
async def get_options():
    """下发 14 维度选项定义、内置预设与模型档位配置。"""
    llm_enabled = settings.resolved_provider != "mock"
    tiers = []
    if llm_enabled:
        for tid in ("default", "nano", "mid", "pro"):
            configured = settings.tier_configured(tid)
            # 前端只展示「默认 + 已配置档位」；全部未配置时仅默认
            if tid == "default" or configured:
                tiers.append({
                    "id": tid,
                    "label": TIER_LABELS[tid],
                    "configured": configured,
                })
    return {
        "groups": GROUPS,
        "presets": PRESETS,
        "models": {"llm_enabled": llm_enabled, "tiers": tiers},
    }
