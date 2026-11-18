"""LangGraph 生成工作流（P1 标准模式）。

parse_intent → enrich_details → conflict_check → assemble → refine

- provider=mock（.env 留空时的默认）：节点走本地规则/模板逻辑，全程不联网；
- 配置了 LLM：parse_intent / enrich_details / refine 走模型（OpenAI 兼容协议），
  结构化输出，失败时降级为 mock 逻辑，保证生成链路永不断。

对外暴露 stream_generation()：异步生成器，产出 SSE 事件并负责落库。
"""

import asyncio
import json
import logging

from langgraph.graph import END, START, StateGraph

from app.agent import assemble as assemble_mod
from app.agent.prompt_loader import load_prompt
from app.agent.rules import check_conflicts
from app.agent.state import GenState
from app.core.config import settings
from app.core.llm import get_chat_model

logger = logging.getLogger(__name__)

NODES = ["parse_intent", "enrich_details", "conflict_check", "assemble", "refine"]

MOCK_STEP_DELAY = 0.3  # mock 模式下每步稍作停顿，与 P0 原型的分步动画体验对齐


# ─────────────────────────── 节点实现 ───────────────────────────

async def parse_intent(state: GenState) -> dict:
    """解析主题意图。主题为空 → 跳过（氛围模式）。"""
    theme = state["theme"].strip()
    if not theme:
        return {"parsed": None}
    llm = get_chat_model(temperature=0.3)
    if llm is not None:
        try:
            from pydantic import BaseModel

            class Intent(BaseModel):
                subject: str = ""
                action: str = ""
                scene: str = ""
                summary: str = ""

            result = await llm.with_structured_output(Intent).ainvoke(
                load_prompt("parse_intent", theme=theme)
            )
            return {"parsed": result.model_dump()}
        except Exception:
            logger.exception("parse_intent LLM 调用失败，降级为本地解析")
    # mock / 降级：主题本身即主体
    return {"parsed": {"subject": theme, "action": "", "scene": "", "summary": theme}}


async def enrich_details(state: GenState) -> dict:
    """按创意自由度补全未选择维度的细节建议（只进 notes，不覆盖用户选择）。"""
    creative = state["selections"].get("creative")
    if creative != "充分发挥" or not state["theme"].strip():
        return {"enriched": []}
    llm = get_chat_model(temperature=0.9)
    if llm is not None:
        try:
            chosen = {k: v for k, v in state["selections"].items() if v}
            result = await llm.ainvoke(
                load_prompt(
                    "enrich_details",
                    theme=state["theme"].strip(),
                    selections=json.dumps(chosen, ensure_ascii=False),
                )
            )
            lines = [ln.strip("-• ") for ln in result.content.splitlines() if ln.strip()]
            return {"enriched": lines[:3]}
        except Exception:
            logger.exception("enrich_details LLM 调用失败，跳过补全")
    return {"enriched": []}


async def conflict_check(state: GenState) -> dict:
    notes, warnings = check_conflicts(state["selections"])
    return {"rule_notes": notes, "rule_warnings": warnings}


async def assemble(state: GenState) -> dict:
    result = assemble_mod.assemble(
        state["selections"],
        state["theme"],
        rule_notes=state.get("rule_notes"),
        rule_warnings=state.get("rule_warnings"),
    )
    return {"draft": result["prompt"], "final": {**result, "notes": result["notes"] + [
        {"rule": "enrich", "message": f"细节建议：{s}"} for s in state.get("enriched", [])
    ]}}


async def refine(state: GenState) -> dict:
    """润色自检。mock 模式直接透传初稿（初稿已含规则修正）。"""
    llm = get_chat_model(temperature=0.6)
    if llm is None:
        return {"final": state["final"]}
    try:
        from pydantic import BaseModel, Field

        class FinalPrompt(BaseModel):
            prompt: str = Field(description="润色后的完整提示词")
            polish_notes: list[str] = Field(default_factory=list, description="润色说明，每条一句")

        result = await llm.with_structured_output(FinalPrompt).ainvoke(
            load_prompt("refine", draft=state["draft"])
        )
        final = dict(state["final"])
        final["prompt"] = result.prompt
        final["notes"] = final["notes"] + [
            {"rule": "polish", "message": n} for n in result.polish_notes
        ]
        return {"final": final}
    except Exception:
        logger.exception("refine LLM 调用失败，使用初稿")
        return {"final": state["final"]}


# ─────────────────────────── 图编排 ───────────────────────────

def build_graph():
    g = StateGraph(GenState)
    g.add_node("parse_intent", parse_intent)
    g.add_node("enrich_details", enrich_details)
    g.add_node("conflict_check", conflict_check)
    g.add_node("assemble", assemble)
    g.add_node("refine", refine)
    g.add_edge(START, "parse_intent")
    g.add_edge("parse_intent", "enrich_details")
    g.add_edge("enrich_details", "conflict_check")
    g.add_edge("conflict_check", "assemble")
    g.add_edge("assemble", "refine")
    g.add_edge("refine", END)
    return g.compile()


graph = build_graph()


# ─────────────────────────── SSE 事件流 ───────────────────────────

def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def stream_generation(selections: dict, theme: str, mode: str = "standard"):
    """执行生成图，产出 SSE 文本流；结束后落库并发出 result 事件。

    事件时序：对每个节点先发 running（mock 模式停顿片刻模拟处理耗时），
    再等该节点真实完成发 done；全部完成后落库并发 result。
    """
    from app.db.models import Generation, new_id, now_iso
    from app.db.session import SessionLocal

    init = {"selections": selections, "theme": theme}
    is_mock = settings.resolved_provider == "mock"
    updates: dict = {}
    stream = graph.astream(init, stream_mode="updates")

    for i, node in enumerate(NODES):
        yield sse("step", {"node": node, "status": "running", "index": i})
        if is_mock:
            await asyncio.sleep(MOCK_STEP_DELAY)
        try:
            chunk = await stream.__anext__()
        except StopAsyncIteration:
            break
        except Exception:
            logger.exception("节点 %s 执行失败", node)
            yield sse("error", {"message": f"生成失败于节点 {node}"})
            return
        updates.update(chunk)
        yield sse("step", {"node": node, "status": "done", "index": i})

    # updates 是「节点名 → 节点输出」映射，最终结果由 refine 节点产出
    final = updates.get("refine", {}).get("final", {})
    gen_id = new_id()
    async with SessionLocal() as session:
        session.add(Generation(
            id=gen_id,
            created_at=now_iso(),
            selections=json.dumps(selections, ensure_ascii=False),
            theme=theme,
            final_prompt=final.get("prompt", ""),
            notes=json.dumps(final.get("notes", []), ensure_ascii=False),
            warnings=json.dumps(final.get("warnings", []), ensure_ascii=False),
            model=settings.resolved_provider,
            mode=mode,
        ))
        await session.commit()

    yield sse("result", {
        "id": gen_id,
        "prompt": final.get("prompt", ""),
        "notes": final.get("notes", []),
        "warnings": final.get("warnings", []),
        "suggested_ratio": final.get("suggested_ratio", ""),
        "model": settings.resolved_provider,
    })
