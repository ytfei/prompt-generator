"""主题灵感：基于已选配置批量生成创意主题描述，用于启发灵感。

单次 LLM 调用产出多条候选（避免多次调用的等待），mock / 失败时降级为
本地灵感池随机抽取。
"""

import json
import logging
import random

from app.agent.prompt_loader import load_prompt
from app.core.llm import get_chat_model

logger = logging.getLogger(__name__)

THEME_COUNT = 4

FALLBACK_THEMES = [
    "深夜便利店门口，一个撑伞的人驻足望着积水中霓虹灯的倒影",
    "旧书房的窗台上，一只猫踩过摊开的书页，阳光正好落在铅字上",
    "清晨的菜市场，鱼贩扬起的水珠在逆光中悬停成金色的雾",
    "废弃天文台的穹顶裂缝里，一株野草正对着星空生长",
    "暴雨将至的屋顶天台，晾晒的白床单被狂风吹成鼓胀的帆",
    "老式理发店里，转灯的光影扫过蒙尘的镜面与空荡的座椅",
    "退潮后的滩涂上，一只寄居蟹正搬家，背着比身体大两倍的贝壳",
    "深夜末班地铁的车厢内，乘客的影子被灯光拉长投在天花板上",
    "大雪覆盖的公交站牌下，候车的人呵出白气，睫毛上落了雪",
    "祖屋阁楼的木箱里，一沓老照片散开，最上面那张被阳光晒得褪色",
    "凌晨四点的面馆后厨，蒸汽升腾中老师傅把一团面甩向空中",
    "城市天桥下，卖气球的人在风中攥住一大把挣脱的彩色气球",
]


def _clean_lines(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        line = raw.strip().lstrip("0123456789.-•*）) ").strip().strip('"').strip("「」")
        if line:
            lines.append(line)
    return lines


async def inspire_themes(selections: dict, tier: str = "default", theme: str = "") -> list[str]:
    chosen = {k: v for k, v in (selections or {}).items() if v}
    selections_json = json.dumps(chosen, ensure_ascii=False)
    llm = get_chat_model(temperature=1.0, tier=tier)
    if llm is None:
        return random.sample(FALLBACK_THEMES, THEME_COUNT)
    try:
        # 有主题 → 围绕用户主题做变体；无主题 → 按配置发散
        prompt = (
            load_prompt("inspire_from_theme", theme=theme.strip(), selections=selections_json)
            if theme.strip()
            else load_prompt("inspire_theme", selections=selections_json)
        )
        result = await llm.ainvoke(prompt)
        themes = _clean_lines(result.content)[:THEME_COUNT]
        if not themes:
            return random.sample(FALLBACK_THEMES, THEME_COUNT)
        return themes
    except Exception:
        logger.exception("inspire_themes LLM 调用失败，降级为本地灵感池")
        return random.sample(FALLBACK_THEMES, THEME_COUNT)
