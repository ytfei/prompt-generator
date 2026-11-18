"""提示词组装引擎：把选项 + 主题拼装为结构化中文提示词。

mock 模式下的主力逻辑（平移自 P0 原型）；真实 LLM 模式下其产物作为
assemble 节点初稿，再由 refine 节点润色。
"""

from app.agent.options_data import GROUPS
from app.agent.rules import check_conflicts


def option_prompt(gid: str, label: str | None) -> str:
    if not label:
        return ""
    opt = next((o for o in GROUPS[gid]["options"] if o["label"] == label), None)
    return (opt or {}).get("prompt", "")


def usage_ratio(usage: str | None) -> str:
    if not usage:
        return ""
    opt = next((o for o in GROUPS["usage"]["options"] if o["label"] == usage), None)
    return (opt or {}).get("ratio", "")


def assemble(
    selections: dict,
    theme: str,
    rule_notes: list[dict] | None = None,
    rule_warnings: list[dict] | None = None,
) -> dict:
    """组装初稿。返回 {prompt, notes, warnings, suggested_ratio}。

    rule_notes / rule_warnings：conflict 节点已算好的规则结果；不传则现场计算。
    """
    if rule_notes is not None and rule_warnings is not None:
        notes, warnings = list(rule_notes), list(rule_warnings)
    else:
        notes, warnings = check_conflicts(selections)
    tone = option_prompt("tone", selections.get("tone"))

    # 规则命中的情绪×色调冲突：mock 模式直接改写色调片段
    mood_tone = next((n for n in notes if n["rule"] == "mood_tone"), None)
    if mood_tone:
        tone = mood_tone["suggest_tone_prompt"]

    parts: list[str] = []
    parts.append(option_prompt("style", selections.get("style")))
    parts.append(option_prompt("genre", selections.get("genre")))

    if theme.strip():
        parts.append(f"画面主体：{theme.strip()}")
    else:
        parts.append("一幅氛围感画面，主体自然融入环境")
        warnings.append({
            "rule": "empty_theme",
            "message": "主题描述为空：已生成氛围型提示词，补充主题可获得更精准的结果",
        })

    bg = option_prompt("bg", selections.get("bg"))
    if bg:
        parts.append(f"背景为{bg}")
    parts.append(option_prompt("light", selections.get("light")))
    parts.append(tone)
    parts.append(option_prompt("comp", selections.get("comp")))
    parts.append(option_prompt("shot", selections.get("shot")))
    mood_p = option_prompt("mood", selections.get("mood"))
    if mood_p:
        parts.append(f"整体{mood_p}")
    tex = option_prompt("texture", selections.get("texture"))
    if tex:
        parts.append(f"呈现{tex}")
    parts.append(option_prompt("text", selections.get("text")))

    creative = selections.get("creative")
    parts.append(option_prompt("creative", creative))

    parts.append("超高细节，画质精致")

    ratio = selections.get("ratio") or usage_ratio(selections.get("usage"))
    if ratio:
        parts.append(f"画幅比例 {ratio}")

    prompt = "，".join(p for p in parts if p) + "。"

    negs = selections.get("negative") or []
    if negs:
        neg_phrases = [option_prompt("negative", n) or f"不出现{n}" for n in negs]
        prompt += " 避免出现：" + "，".join(neg_phrases) + "。"

    if creative == "充分发挥" and theme.strip():
        notes.append({
            "rule": "creative_free",
            "message": "已按「充分发挥」自由度预留创意补全空间（接入真实 LLM 后将自动扩写细节）",
        })
    if selections.get("usage") and ratio and ratio == usage_ratio(selections.get("usage")):
        notes.append({
            "rule": "ratio_aligned",
            "message": f"画幅 {ratio} 已与用途「{selections['usage']}」对齐",
        })

    return {"prompt": prompt, "notes": notes, "warnings": warnings, "suggested_ratio": ratio}
