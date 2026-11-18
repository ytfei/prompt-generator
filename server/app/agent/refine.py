"""多轮迭代：基于已有生成结果，按用户指令继续修改（P2-4）。

- LangGraph 图：apply_instruction → conflict_scan；
- AsyncSqliteSaver 以根生成 id 为 thread_id，跨多次迭代保留对话状态，
  "再改一次"直接在同一线程上继续；
- 每次迭代落库为新行（mode='refine'，parent_id 指向上一条），历史可追溯；
- mock 模式（未配 LLM）降级为显式追加调整要求，保证链路可用。
"""

import asyncio
import json
import logging

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from app.agent.prompt_loader import load_prompt
from app.agent.rules import check_conflicts
from app.core.config import settings
from app.core.llm import get_chat_model

logger = logging.getLogger(__name__)

REFINE_NODES = ["apply_instruction", "conflict_scan"]

# 与 graph.py 的 mock 分步停顿保持一致的体验
MOCK_STEP_DELAY = 0.3


class RefineState(TypedDict, total=False):
    base_prompt: str  # 首次迭代的原始提示词
    selections: dict  # 原始维度选择（用于冲突扫描）
    instruction: str  # 本次修改要求
    tier: str  # 模型档位
    final: dict  # {prompt, notes}（随迭代更新，checkpointer 持久化）
    warnings: list[dict]  # conflict_scan 产出


async def apply_instruction(state: RefineState) -> dict:
    current = state.get("final", {}).get("prompt") or state["base_prompt"]
    instruction = state["instruction"].strip()
    llm = get_chat_model(temperature=0.5, tier=state.get("tier", "default"))
    if llm is None:
        # mock 降级：显式标注调整要求，接入真实模型后由 LLM 真正改写
        prompt = f"{current}（调整要求：{instruction}）"
        note = {"rule": "refine_mock", "message": f"mock 模式：已追加调整要求「{instruction}」，接入真实模型后生效"}
    else:
        try:
            result = await llm.ainvoke(
                load_prompt("refine_instruction", prompt=current, instruction=instruction)
            )
            prompt = result.content.strip()
            note = {"rule": "refine", "message": f"已按要求修改：{instruction}"}
        except Exception:
            logger.exception("apply_instruction LLM 调用失败，降级为追加指令")
            prompt = f"{current}（调整要求：{instruction}）"
            note = {"rule": "refine_fallback", "message": f"模型调用失败，已追加调整要求「{instruction}」"}

    notes = list(state.get("final", {}).get("notes", [])) + [note]
    return {"final": {"prompt": prompt, "notes": notes}}


async def conflict_scan(state: RefineState) -> dict:
    _, warnings = check_conflicts(state.get("selections", {}))
    return {"warnings": warnings}


_refine_graph = None
_saver: AsyncSqliteSaver | None = None


async def setup_refine(db_path: str) -> None:
    """应用启动时打开 checkpointer 连接并编译 refine 图。"""
    import aiosqlite

    global _refine_graph, _saver
    if _refine_graph is not None:
        return
    conn = await aiosqlite.connect(db_path)
    _saver = AsyncSqliteSaver(conn)
    await _saver.setup()

    g = StateGraph(RefineState)
    g.add_node("apply_instruction", apply_instruction)
    g.add_node("conflict_scan", conflict_scan)
    g.add_edge(START, "apply_instruction")
    g.add_edge("apply_instruction", "conflict_scan")
    g.add_edge("conflict_scan", END)
    _refine_graph = g.compile(checkpointer=_saver)


async def teardown_refine() -> None:
    """关闭 checkpointer 连接。aiosqlite 线程非 daemon，不关会导致进程无法退出。"""
    global _refine_graph, _saver
    if _saver is not None:
        await _saver.conn.close()
    _refine_graph = None
    _saver = None


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _resolve_root(gen_id: str) -> str:
    """沿 parent_id 链回溯到根生成（checkpointer 线程 id）。"""
    from app.db.models import Generation
    from app.db.session import SessionLocal

    current = gen_id
    for _ in range(32):  # 防御环/超长链
        async with SessionLocal() as session:
            row = await session.get(Generation, current)
        if row is None or not row.parent_id:
            return current
        current = row.parent_id
    return current


async def stream_refine(
    gen_id: str, base_prompt: str, selections: dict, instruction: str, tier: str = "default"
):
    """执行一次迭代：SSE 步骤流 + 落库新行 + result 事件。"""
    from app.db.models import Generation, new_id, now_iso
    from app.db.session import SessionLocal

    if _refine_graph is None:
        yield sse("error", {"message": "refine 图未初始化"})
        return

    root_id = await _resolve_root(gen_id)
    thread = {"configurable": {"thread_id": root_id}}
    is_mock = settings.resolved_provider == "mock"
    model_tag = settings.resolved_provider if is_mock else (
        f"{settings.resolved_provider}:{settings.model_for_tier(tier)}"
    )
    updates: dict = {}
    stream = _refine_graph.astream(
        {
            "base_prompt": base_prompt,
            "selections": selections,
            "instruction": instruction,
            "tier": tier,
        },
        thread,
        stream_mode="updates",
    )

    for i, node in enumerate(REFINE_NODES):
        yield sse("step", {"node": node, "status": "running", "index": i})
        if is_mock:
            await asyncio.sleep(MOCK_STEP_DELAY)
        try:
            chunk = await stream.__anext__()
        except StopAsyncIteration:
            break
        except Exception:
            logger.exception("迭代节点 %s 执行失败", node)
            yield sse("error", {"message": f"迭代失败于节点 {node}"})
            return
        updates.update(chunk)
        yield sse("step", {"node": node, "status": "done", "index": i})

    final = updates.get("apply_instruction", {}).get("final")
    warnings = updates.get("conflict_scan", {}).get("warnings", [])
    if final is None:
        final = {"prompt": "", "notes": []}

    new_id_ = new_id()
    async with SessionLocal() as session:
        session.add(Generation(
            id=new_id_,
            created_at=now_iso(),
            selections=json.dumps(selections, ensure_ascii=False),
            theme="",
            final_prompt=final["prompt"],
            notes=json.dumps(final["notes"], ensure_ascii=False),
            warnings=json.dumps(warnings, ensure_ascii=False),
            model=model_tag,
            mode="refine",
            parent_id=gen_id,
        ))
        await session.commit()

    yield sse("result", {
        "id": new_id_,
        "prompt": final["prompt"],
        "notes": final["notes"],
        "warnings": warnings,
        "suggested_ratio": "",
        "model": model_tag,
        "parent_id": gen_id,
    })
