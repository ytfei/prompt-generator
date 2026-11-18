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


class I2IState(TypedDict, total=False):
    """图生图工作流状态（i2i.py）。"""

    # 输入
    desc: str  # 图片内容描述（必填）
    scene: str  # creative / modify / style
    direction: str  # 创意方向（creative 场景，可空）
    style: str  # 目标风格（style 场景，可空）
    modify: str  # 修改意向（modify 场景）
    ratio: str  # 目标画幅（扩图模板联动，可空）
    template: str  # 套用的修改模板 id（可空）
    tier: str
    # 节点产物
    summary: str  # understand_image：原图要素概括
    finals: list[dict]  # align_intent：[{direction, note, prompt}]（creative 3 条，其余 1 条）
    warnings: list[dict]  # fusion_check：融合质量警告
    notes: list[dict]
    final: dict  # compose：{finals, notes, warnings, suggested_ratio}
