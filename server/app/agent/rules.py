"""维度间冲突检查（纯规则，零 token）。返回需写入优化说明/警告的条目。"""

QUIET_MOODS = {"忧郁孤独", "宁静平和"}
LOUD_TONES = {"高饱和", "霓虹撞色"}


def check_conflicts(selections: dict) -> tuple[list[dict], list[dict]]:
    """返回 (notes, warnings)。

    notes：Agent 已自动修正的事项；warnings：需要用户留意但未自动改动的事项。
    """
    notes: list[dict] = []
    warnings: list[dict] = []

    mood = selections.get("mood")
    tone = selections.get("tone")

    # 情绪 × 色调：忧郁/宁静 × 高饱和冲突 → 建议调整（mock 模式直接改写片段）
    if mood in QUIET_MOODS and tone in LOUD_TONES:
        notes.append({
            "rule": "mood_tone",
            "message": f"检测到「{mood}」与「{tone}」存在情绪冲突，建议调整为低饱和柔和表述",
            "suggest_tone_prompt": "低饱和柔和色彩，克制而统一",
        })

    # 用途 × 画幅
    usage, ratio = selections.get("usage"), selections.get("ratio")
    usage_ratio = ""
    if usage:
        from app.agent.options_data import GROUPS

        opt = next((o for o in GROUPS["usage"]["options"] if o["label"] == usage), None)
        usage_ratio = (opt or {}).get("ratio", "")
    if usage and ratio and usage_ratio and ratio != usage_ratio:
        warnings.append({
            "rule": "usage_ratio",
            "message": f"所选画幅 {ratio} 与用途「{usage}」推荐画幅 {usage_ratio} 不一致，"
                       f"建议在即梦中以 {usage_ratio} 出图",
        })

    # 文字 × 负向：要求含文字但排除乱码 → 强调文字清晰
    text, negs = selections.get("text"), selections.get("negative") or []
    if text == "含标题文字" and "文字乱码" in negs:
        notes.append({
            "rule": "text_negative",
            "message": "已强调「文字清晰可读、无乱码」，与排除项保持一致",
        })

    return notes, warnings
