from app.agent.assemble import assemble
from app.agent.rules import check_conflicts


def test_basic_assembly_contains_selections():
    result = assemble(
        {"style": "手绘水彩", "tone": "暖调", "ratio": "16:9", "creative": "平衡"},
        "一只猫在窗台晒太阳",
    )
    assert "水彩手绘风格" in result["prompt"]
    assert "画面主体：一只猫在窗台晒太阳" in result["prompt"]
    assert "整体暖色调" in result["prompt"]
    assert "画幅比例 16:9" in result["prompt"]
    assert result["prompt"].endswith("。")


def test_empty_theme_produces_warning():
    result = assemble({"style": "油画"}, "")
    assert any(w["rule"] == "empty_theme" for w in result["warnings"])
    assert "一幅氛围感画面" in result["prompt"]


def test_mood_tone_conflict_rewrites_tone():
    notes, _ = check_conflicts({"mood": "忧郁孤独", "tone": "高饱和"})
    assert notes and notes[0]["rule"] == "mood_tone"
    result = assemble({"mood": "忧郁孤独", "tone": "高饱和"}, "雨夜街道")
    assert "高饱和浓郁色彩" not in result["prompt"]
    assert "低饱和柔和色彩" in result["prompt"]


def test_usage_ratio_mismatch_warns():
    _, warnings = check_conflicts({"usage": "公众号首图", "ratio": "1:1"})
    assert any(w["rule"] == "usage_ratio" for w in warnings)


def test_usage_default_ratio_used_when_ratio_unset():
    result = assemble({"usage": "公众号首图"}, "城市夜景")
    assert "画幅比例 2.35:1" in result["prompt"]


def test_negative_prompts_appended():
    result = assemble({"negative": ["水印", "低质量"]}, "咖啡杯")
    assert "避免出现" in result["prompt"]
    assert "无水印" in result["prompt"]
