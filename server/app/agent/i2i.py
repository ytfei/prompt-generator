"""图生图提示词生成工作流（PRD v0.2 M10）。

understand_image → align_intent → fusion_check → compose

- provider=mock（.env 留空时的默认）：节点走本地模板逻辑，全程不联网；
- 配置了 LLM：understand_image / align_intent 走模型（OpenAI 兼容协议），
  失败时降级为本地模板，保证链路永不断；
- 融合质量检查（fusion_check）为纯 Python 规则，不烧 token。

与文生图的差异：图生图提示词的核心结构是「保持原图约束 + 修改/创意指令」；
创意灵感场景一次产出 3 条（finals 列表），其余场景 1 条。

对外暴露 stream_i2i()：异步生成器，产出 SSE 事件并负责落库（mode='i2i'）。
"""

import asyncio
import json
import logging
import re

from langgraph.graph import END, START, StateGraph

from app.agent.i2i_data import I2I_DIRS, I2I_TEMPLATES, OUTPAINT_DEFAULT_RATIO
from app.agent.prompt_loader import load_prompt
from app.agent.state import I2IState
from app.core.config import settings
from app.core.llm import get_chat_model

logger = logging.getLogger(__name__)

I2I_NODES = ["understand_image", "align_intent", "fusion_check", "compose"]

MOCK_STEP_DELAY = 0.3

# 判断描述中是否出现人物的关键词（人像精修冲突检查用）
_PERSON_RE = re.compile(
    r"人像|人物|肖像|头像|自拍|模特|女孩|男孩|女人|男人|女士|先生|老人|小孩|儿童|婴儿|帅哥|美女|脸|他|她|我"
)

CARD_SEP = "\n===\n"  # 多条提示词落库时的分隔符


def _template_text(tpl_id: str) -> str:
    return next((t["text"] for t in I2I_TEMPLATES if t["id"] == tpl_id), "")


# ─────────────────────────── 节点实现 ───────────────────────────


async def understand_image(state: I2IState) -> dict:
    """从文字描述中概括原图要素。mock：描述本身即概括。"""
    desc = state["desc"].strip()
    llm = get_chat_model(temperature=0.3, tier="nano")
    if llm is not None:
        try:
            result = await llm.ainvoke(load_prompt("i2i_understand", desc=desc))
            summary = result.content.strip().splitlines()[0].strip()
            if summary:
                return {"summary": summary}
        except Exception:
            logger.exception("understand_image LLM 调用失败，降级为原描述")
    return {"summary": desc}


async def _creative_llm(
    desc: str, direction: str, direction_tip: str, modify: str, tier: str
) -> list[dict] | None:
    """创意灵感：单次调用产出 3 条结构化提示词。"""
    from pydantic import BaseModel, Field

    class CreativePrompt(BaseModel):
        direction: str = Field(description="这条提示词的创意方向名")
        note: str = Field(description="一句话说明这条的方向")
        prompt: str = Field(description="完整提示词")

    class CreativeSet(BaseModel):
        prompts: list[CreativePrompt] = Field(min_length=3, max_length=3)

    llm = get_chat_model(temperature=0.9, tier=tier)
    if llm is None:
        return None
    try:
        result = await llm.with_structured_output(CreativeSet).ainvoke(
            load_prompt(
                "i2i_creative",
                desc=desc,
                direction=direction,
                direction_tip=direction_tip,
                modify_ref=modify_ref_sentence(modify),
            )
        )
        return [p.model_dump() for p in result.prompts]
    except Exception:
        logger.exception("creative LLM 调用失败，降级为本地模板")
        return None


def modify_ref_sentence(modify: str) -> str:
    """把修改意向转成提示词模板中的一句话；空意向 = 自由发挥。"""
    modify = modify.strip()
    if not modify:
        return "用户未填写修改意向，此条请自由发挥。"
    return f"用户还给出了修改意向：「{modify}」。请在创意发散时把该意向融入每条提示词。"


def _creative_mock(desc: str, direction: str, modify: str) -> list[dict]:
    """mock / LLM 降级用：按方向给出 3 条不同切入角度的提示词。

    每个方向配 3 个 (副标签, 创意指令)；未收录方向回退为自由脑洞三方向。
    修改意向非空时融入每条提示词。
    """
    angles = _DIRECTION_ANGLES.get(direction)
    if not angles:
        return _creative_freehold(desc, modify)
    base = f"参考原图内容：{desc}"
    ref = f"用户修改意向（请一并体现）：{modify.strip()}。" if modify.strip() else ""
    return [
        {
            "direction": direction,
            "note": f"{direction} · {sub}",
            "prompt": f"{base}。创意要求（{direction}）：{instruction}{ref}保持原图主体可识别，超高细节，画质精致。",
        }
        for sub, instruction in angles
    ]


def _creative_freehold(desc: str, modify: str = "") -> list[dict]:
    """「自由脑洞」或未收录方向：三个方向各出一条。"""
    base = f"参考原图内容：{desc}"
    ref = f"同时参考用户修改意向：{modify.strip()}。" if modify.strip() else ""
    return [
        {
            "direction": "系列延展",
            "note": "系列延展 · 同风格成套",
            "prompt": f"{base}。以同风格延展一组系列配图：保持主体形象、色调与光线一致，景别依次切换（近景→中景→全景），构图预留标题位，形成成套连载的系列感。{ref}超高细节，画质精致。",
        },
        {
            "direction": "换风格演绎",
            "note": "换风格演绎 · 换一种画风",
            "prompt": f"{base}。将同一内容以「手绘水彩」风格重新演绎：保留原图主体与场景关系，笔触、色彩与质感替换为水彩语言，颜料晕染通透自然。{ref}超高细节，画质精致。",
        },
        {
            "direction": "场景延伸",
            "note": "场景延伸 · 场景向外发散",
            "prompt": f"{base}。延续原图主体，将场景向画面边界外延展：补充合理的环境细节，主体保持在视觉中心，整体氛围连贯统一。{ref}超高细节，画质精致。",
        },
    ]


# 各创意方向的 3 个 mock 切入角度：(副标签, 创意指令)
_DIRECTION_ANGLES: dict[str, list[tuple[str, str]]] = {
    "系列延展": [
        ("递进一", "同款主体、同款色调光线，景别推进至近景，强调主体细节，成套使用。"),
        ("递进二", "同款主体、同款色调光线，景别推进至中景，主体与环境并重，构图预留标题位。"),
        ("递进三", "同款主体、同款色调光线，景别推进至全景，展现完整场景氛围。"),
    ],
    "换风格演绎": [
        (
            "手绘水彩",
            "将画面以「手绘水彩」风格重新演绎：笔触、色彩与质感替换为水彩语言，颜料晕染通透自然。",
        ),
        ("国风水墨", "将画面以「国风水墨」风格重新演绎：写意笔触与留白意境，墨色浓淡相宜。"),
        ("3D渲染", "将画面以「3D渲染(C4D)」风格重新演绎：立体精致富有体积感，材质细腻。"),
    ],
    "场景延伸": [
        ("向四周展开", "将场景向画面边界外延展：补充合理的环境细节，主体保持在视觉中心。"),
        ("向纵深延展", "保留主体，画面向纵深延展：补出主体身后更远的背景层次与环境。"),
        ("向上方延伸", "保留主体，画面向上方延伸：补出天空、光照与更高处的环境元素。"),
    ],
    "时光变换": [
        (
            "换季节",
            "把画面迁移到另一个季节：植被、服饰、色调与光线随季节同步变化，主体保持可识别。",
        ),
        ("换昼夜", "把画面迁移到一天中的另一时刻：光线、色温与氛围随之改变，构图与主体不变。"),
        ("换年代", "把画面迁移到另一个年代：环境、道具与质感带出鲜明的时代特征，主体保持可识别。"),
    ],
    "视角再造": [
        ("微距化", "换成微距视角：贴近主体呈现纤毫毕现的细节，背景虚化，构图重排。"),
        ("高空俯瞰", "换成高空俯瞰视角：从上方重新组织画面，主体与环境的几何关系成为重点。"),
        ("第一人称", "换成第一人称主观视角：让观者以画中人的眼睛看向主体，代入感强。"),
    ],
    "情绪反转": [
        ("转向悬疑", "保持画面内容不变，将情绪氛围转向神秘悬疑：光影收紧、色调变冷、阴影加深。"),
        ("转向治愈", "保持画面内容不变，将情绪氛围转向治愈温暖：光线变柔、色调转暖、氛围松弛。"),
        (
            "转向荒诞幽默",
            "保持画面内容不变，将情绪氛围转向幽默荒诞：加入出人意料的趣味元素与夸张对比。",
        ),
    ],
    "跨界混搭": [
        (
            "闯入赛博都市",
            "让画面主体闯入赛博朋克未来都市：霓虹光、全息投影与雨夜街道，主体与环境碰撞融合。",
        ),
        (
            "闯入水墨山水",
            "让画面主体进入中国水墨山水：写意笔触的山川云雾，主体以水墨语言重新呈现。",
        ),
        ("闯入微观世界", "把画面主体缩小放进微观世界：苔藓成森林、水珠成湖泊，比例反差制造奇观。"),
    ],
    "拟人拟物": [
        ("物件拟人", "让画面中的关键物件拟人化：拥有表情、姿态与性格，主体与环境保持原样。"),
        ("物种变换", "把画面主体变换为另一种生物或物种：保留原有的动作、位置与构图关系。"),
        ("角色互换", "让画面中的主体与配角元素互换角色：位置、大小与身份对调，制造新鲜感。"),
    ],
    "故事续写": [
        (
            "前一秒",
            "想象画面定格前的最后一刻：交代动作的起因与即将发生的变化，与原图同风格同场景。",
        ),
        ("后一刻", "想象画面定格后的下一刻：动作的结果与环境的反应，与原图同风格同场景。"),
        ("画外延伸", "画出画面之外正在发生的另一幕：与原图同时同地、风格一致，但视角转向画外。"),
    ],
    "细节放大": [
        (
            "角落小物成主角",
            "把画面角落里的一个小物件放大为主角：微距呈现它的细节，原场景虚化为背景。",
        ),
        ("纹理质感特写", "聚焦画面中最有质感的纹理表面：放大呈现材质细节，光影突出肌理。"),
        ("以小见大", "用一个小细节暗示整个画面：特写局部，让观者从细节联想完整场景。"),
    ],
    "极简海报": [
        ("几何提炼", "把画面提炼成海报级极简构图：主体简化为基本几何形态，色彩克制。"),
        ("大面积留白", "把画面重构成大面积留白的海报：主体精炼置于黄金分割点，留白处可放标题。"),
        ("单色聚焦", "把画面提炼为单色系海报：主体保留唯一强调色，其余统一为同色系层次。"),
    ],
}


async def _modify_llm(desc: str, modify: str, ratio: str, tier: str) -> str | None:
    llm = get_chat_model(temperature=0.5, tier=tier)
    if llm is None:
        return None
    try:
        result = await llm.ainvoke(
            load_prompt("i2i_modify", desc=desc, modify=modify, ratio=ratio or "无")
        )
        text = result.content.strip()
        return text or None
    except Exception:
        logger.exception("modify LLM 调用失败，降级为本地模板")
        return None


def _modify_mock(desc: str, modify: str, ratio: str) -> str:
    prompt = (
        f"参考原图：{desc}。修改要求：{modify}。"
        "保持原图的主体、构图与整体风格不变，仅执行上述修改，"
        "修改区域与原图光影、透视、色调自然融合，过渡无痕，画质保持高清。"
        "避免出现：修改痕迹明显、边缘锯齿、构图偏移。"
    )
    if ratio:
        prompt += f" 画幅比例 {ratio}。"
    return prompt


async def _style_llm(desc: str, style: str, modify: str, tier: str) -> str | None:
    llm = get_chat_model(temperature=0.6, tier=tier)
    if llm is None:
        return None
    try:
        result = await llm.ainvoke(
            load_prompt("i2i_style", desc=desc, style=style, modify_ref=modify_ref_sentence(modify))
        )
        text = result.content.strip()
        return text or None
    except Exception:
        logger.exception("style LLM 调用失败，降级为本地模板")
        return None


def _style_mock(desc: str, style: str, modify: str) -> str:
    ref = f"同时参考用户修改意向：{modify.strip()}。" if modify.strip() else ""
    return (
        f"参考原图：{desc}。将整幅画面转换为「{style}」风格："
        "保留原图的构图、主体与空间关系，色彩、笔触与质感整体按目标风格重新呈现，"
        f"转换后画面完整、细节丰富、风格统一。{ref}超高细节，画质精致。"
    )


async def align_intent(state: I2IState) -> dict:
    """按场景生成提示词内容（LLM 或本地模板）。

    修改意向（modify）对三个场景通用：填写则参考，留空则自由发挥。
    """
    desc = state["summary"] or state["desc"].strip()
    scene = state["scene"]
    tier = state.get("tier", "default")
    modify = state.get("modify", "").strip()

    if scene == "creative":
        direction = state.get("direction") or "自由脑洞"
        dir_tip = next((d["tip"] for d in I2I_DIRS if d["label"] == direction), "混合发散")
        finals = await _creative_llm(desc, direction, dir_tip, modify, tier) or _creative_mock(
            desc, direction, modify
        )
        notes = (
            []
            if state.get("direction")
            else [
                {
                    "rule": "i2i_dir_default",
                    "message": "未指定创意方向，已按「自由脑洞」给出三个方向各一条",
                }
            ]
        )
        if modify:
            notes.append({"rule": "i2i_modify_ref", "message": f"已参考修改意向：{modify}"})
        return {"finals": finals, "notes": notes}

    if scene == "modify":
        if not modify:
            # 空修改意向：通用画质增强兜底（compose 会补警告）
            fallback = (
                f"参考原图：{desc}。在保持原图主体、构图与风格完全不变的前提下，"
                "提升整体画质：增强清晰度与细节，优化光影层次，画面更通透。"
                "避免出现：修改痕迹明显、构图偏移。"
            )
            return {"finals": [{"direction": "modify", "note": "通用画质增强", "prompt": fallback}]}
        text = await _modify_llm(desc, modify, state.get("ratio", ""), tier) or _modify_mock(
            desc, modify, state.get("ratio", "")
        )
        return {"finals": [{"direction": "modify", "note": "精准修改", "prompt": text}]}

    # style
    style = state.get("style") or "由 Agent 依原图内容推荐的最合适风格"
    text = await _style_llm(desc, style, modify, tier) or _style_mock(desc, style, modify)
    notes = (
        []
        if state.get("style")
        else [
            {
                "rule": "i2i_style_default",
                "message": "未指定目标风格，真实 Agent 将分析原图后自动推荐",
            }
        ]
    )
    if modify:
        notes.append({"rule": "i2i_modify_ref", "message": f"已参考修改意向：{modify}"})
    return {
        "finals": [{"direction": "style", "note": f"风格转换 · {style}", "prompt": text}],
        "notes": notes,
    }


async def fusion_check(state: I2IState) -> dict:
    """融合质量规则检查（纯 Python，零 token）。模板是精准修改专属，检查仅在该场景生效。"""
    warnings: list[dict] = []
    if state["scene"] == "modify":
        desc = state["desc"].strip()
        tpl = state.get("template") or ""
        if tpl == "portrait" and not _PERSON_RE.search(desc):
            warnings.append(
                {
                    "rule": "i2i_portrait_no_person",
                    "message": "图片描述中未提到人物，「人像精修」可能无人像可修，请确认原图内容",
                }
            )
        if tpl == "restore" and re.search(r"科技|城市夜景|数码", desc):
            warnings.append(
                {
                    "rule": "i2i_restore_mismatch",
                    "message": "图片描述看起来不是老照片场景，请确认是否需要「老照片修复」",
                }
            )
    return {"warnings": warnings}


async def compose(state: I2IState) -> dict:
    """整理最终输出：扩图补默认画幅、附警告与说明。"""
    finals = state.get("finals", [])
    notes = list(state.get("notes", []))
    warnings = list(state.get("warnings", []))
    suggested_ratio = ""

    if state["scene"] == "modify" and not state["modify"].strip():
        warnings.append(
            {
                "rule": "i2i_empty_modify",
                "message": "修改意向为空：已生成通用的画质增强提示词，补充具体修改意向可获得更精准结果",
            }
        )

    if state["scene"] == "modify" and (state.get("template") or "") == "outpaint":
        ratio = state.get("ratio", "")
        if not ratio:
            ratio = OUTPAINT_DEFAULT_RATIO
            notes.append(
                {
                    "rule": "i2i_outpaint_ratio",
                    "message": f"未选择目标画幅，已按公众号首图默认 {OUTPAINT_DEFAULT_RATIO} 处理",
                }
            )
        else:
            notes.append(
                {"rule": "i2i_outpaint_ratio", "message": f"扩图目标画幅 {ratio} 已写入提示词"}
            )
        suggested_ratio = ratio
        finals = [dict(f, prompt=f"{f['prompt']} 画幅比例 {ratio}。") for f in finals]

    return {
        "final": {
            "finals": finals,
            "notes": notes,
            "warnings": warnings,
            "suggested_ratio": suggested_ratio,
        }
    }


# ─────────────────────────── 图编排 ───────────────────────────


def build_i2i_graph():
    g = StateGraph(I2IState)
    g.add_node("understand_image", understand_image)
    g.add_node("align_intent", align_intent)
    g.add_node("fusion_check", fusion_check)
    g.add_node("compose", compose)
    g.add_edge(START, "understand_image")
    g.add_edge("understand_image", "align_intent")
    g.add_edge("align_intent", "fusion_check")
    g.add_edge("fusion_check", "compose")
    g.add_edge("compose", END)
    return g.compile()


i2i_graph = build_i2i_graph()


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def join_prompts(finals: list[dict]) -> str:
    """多条提示词落库为一段文本，历史页可直接阅读。"""
    return CARD_SEP.join(f"【{f['note']}】\n{f['prompt']}" for f in finals)


async def stream_i2i(payload: dict):
    """执行图生图工作流，产出 SSE 事件流；结束后落库（mode='i2i'）并发 result。"""
    from app.db.models import Generation, new_id, now_iso
    from app.db.session import SessionLocal

    desc = payload.get("desc", "").strip()
    scene = payload.get("scene", "modify")
    tier = payload.get("model_tier", "default")
    init = {
        "desc": desc,
        "scene": scene,
        "direction": payload.get("direction", ""),
        "style": payload.get("style", ""),
        "modify": payload.get("modify", ""),
        "ratio": payload.get("ratio", ""),
        "template": payload.get("template", ""),
        "tier": tier,
    }
    is_mock = settings.resolved_provider == "mock"
    model_tag = (
        settings.resolved_provider
        if is_mock
        else (f"{settings.resolved_provider}:{settings.model_for_tier(tier)}")
    )
    selections = {k: v for k, v in init.items() if k != "tier" and v}

    updates: dict = {}
    stream = i2i_graph.astream(init, stream_mode="updates")

    for i, node in enumerate(I2I_NODES):
        yield sse("step", {"node": node, "status": "running", "index": i})
        if is_mock:
            await asyncio.sleep(MOCK_STEP_DELAY)
        try:
            chunk = await stream.__anext__()
        except StopAsyncIteration:
            break
        except Exception:
            logger.exception("图生图节点 %s 执行失败", node)
            yield sse("error", {"message": f"生成失败于节点 {node}"})
            return
        updates.update(chunk)
        yield sse("step", {"node": node, "status": "done", "index": i})

    final = updates.get("compose", {}).get("final", {})
    finals = final.get("finals", [])
    gen_id = new_id()
    async with SessionLocal() as session:
        session.add(
            Generation(
                id=gen_id,
                created_at=now_iso(),
                selections=json.dumps(selections, ensure_ascii=False),
                theme=desc,
                final_prompt=join_prompts(finals),
                notes=json.dumps(final.get("notes", []), ensure_ascii=False),
                warnings=json.dumps(final.get("warnings", []), ensure_ascii=False),
                model=model_tag,
                mode="i2i",
            )
        )
        await session.commit()

    yield sse(
        "result",
        {
            "id": gen_id,
            "prompts": finals,
            "prompt": join_prompts(finals),
            "notes": final.get("notes", []),
            "warnings": final.get("warnings", []),
            "suggested_ratio": final.get("suggested_ratio", ""),
            "model": model_tag,
        },
    )
