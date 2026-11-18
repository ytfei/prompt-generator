"""LangGraph 图状态定义。节点只读写自己负责的字段。"""

from typing import Any, TypedDict


class ParsedIntent(TypedDict, total=False):
    subject: str  # 主体
    action: str  # 动作
    scene: str  # 场景
    summary: str  # 一句话意图


class GenState(TypedDict, total=False):
    # 输入
    selections: dict[str, Any]
    theme: str
    tier: str  # 模型档位：default / nano / mid / pro
    # 节点产物
    parsed: ParsedIntent | None  # parse_intent：主题解析结果
    enriched: list[str]  # enrich：LLM 补全的细节建议（写进 notes）
    rule_notes: list[dict]  # conflict：规则命中、已自动修正
    rule_warnings: list[dict]  # conflict：需要用户留意
    draft: str  # assemble：提示词初稿
    final: dict  # refine：最终 {prompt, notes, warnings, suggested_ratio}
