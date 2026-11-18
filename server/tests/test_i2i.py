"""图生图链路测试：三场景 SSE 生成、落库、规则警告。全部走 mock 模式。"""

import json

from app.agent.i2i import CARD_SEP, I2I_NODES


def parse_events(text: str) -> list[dict]:
    events = []
    for block in text.split("\n\n"):
        if not block.strip():
            continue
        ev = {}
        for line in block.splitlines():
            if line.startswith("event: "):
                ev["event"] = line[7:]
            elif line.startswith("data: "):
                ev["data"] = json.loads(line[6:])
        events.append(ev)
    return events


async def test_i2i_options_shape(client):
    resp = await client.get("/api/options")
    data = resp.json()
    assert [s["id"] for s in data["i2i"]["scenes"]] == ["creative", "modify", "style"]
    assert len(data["i2i"]["templates"]) == 7
    assert any(t["id"] == "outpaint" for t in data["i2i"]["templates"])


async def test_i2i_modify_scene(client):
    resp = await client.post(
        "/api/i2i-generations",
        json={
            "desc": "一只橘猫趴在窗台上晒太阳",
            "scene": "modify",
            "modify": "把背景换成黄昏的海边",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    events = parse_events(resp.text)
    done_nodes = [
        e["data"]["node"] for e in events if e["event"] == "step" and e["data"]["status"] == "done"
    ]
    assert done_nodes == I2I_NODES

    result = next(e for e in events if e["event"] == "result")["data"]
    assert len(result["prompts"]) == 1
    prompt = result["prompt"]
    assert "参考原图：一只橘猫趴在窗台上晒太阳" in prompt
    assert "修改要求：把背景换成黄昏的海边" in prompt
    assert "保持原图的主体、构图与整体风格不变" in prompt

    # 已落库，mode=i2i
    lst = await client.get("/api/generations")
    row = next(it for it in lst.json() if it["id"] == result["id"])
    assert row["mode"] == "i2i"
    assert row["theme"] == "一只橘猫趴在窗台上晒太阳"
    assert row["selections"]["scene"] == "modify"


async def test_i2i_creative_scene_three_prompts(client):
    resp = await client.post(
        "/api/i2i-generations",
        json={
            "desc": "一杯冒着热气的咖啡放在木桌上",
            "scene": "creative",
        },
    )
    result = next(e for e in parse_events(resp.text) if e["event"] == "result")["data"]
    assert len(result["prompts"]) == 3
    directions = {p["direction"] for p in result["prompts"]}
    assert directions == {"系列延展", "换风格演绎", "场景延伸"}
    # 未指定方向 → 有默认说明 note
    notes = [n["rule"] for n in result["notes"]]
    assert "i2i_dir_default" in notes
    # 落库为拼接文本（含分隔符）
    lst = await client.get("/api/generations")
    row = next(it for it in lst.json() if it["id"] == result["id"])
    assert CARD_SEP in row["final_prompt"]


async def test_i2i_creative_new_direction(client):
    """扩充方向（如跨界混搭）：3 条均落在所选方向上，且无默认说明。"""
    resp = await client.post(
        "/api/i2i-generations",
        json={"desc": "一杯冒着热气的咖啡", "scene": "creative", "direction": "跨界混搭"},
    )
    result = next(e for e in parse_events(resp.text) if e["event"] == "result")["data"]
    assert len(result["prompts"]) == 3
    assert all(p["direction"] == "跨界混搭" for p in result["prompts"])
    assert {p["note"].split(" · ")[1] for p in result["prompts"]} == {
        "闯入赛博都市",
        "闯入水墨山水",
        "闯入微观世界",
    }
    assert not any(n["rule"] == "i2i_dir_default" for n in result["notes"])


async def test_i2i_creative_with_modify_ref(client):
    """修改意向三场景通用：创意场景填写后被参考，留空则自由发挥。"""
    resp = await client.post(
        "/api/i2i-generations",
        json={
            "desc": "一杯冒着热气的咖啡",
            "scene": "creative",
            "direction": "极简海报",
            "modify": "整体色调偏暖",
        },
    )
    result = next(e for e in parse_events(resp.text) if e["event"] == "result")["data"]
    assert all("整体色调偏暖" in p["prompt"] for p in result["prompts"])
    assert any(n["rule"] == "i2i_modify_ref" for n in result["notes"])

    # 留空 → 无参考说明，自由发挥
    resp2 = await client.post(
        "/api/i2i-generations",
        json={"desc": "一杯冒着热气的咖啡", "scene": "creative", "direction": "极简海报"},
    )
    result2 = next(e for e in parse_events(resp2.text) if e["event"] == "result")["data"]
    assert not any(n["rule"] == "i2i_modify_ref" for n in result2["notes"])


async def test_i2i_style_with_modify_ref(client):
    resp = await client.post(
        "/api/i2i-generations",
        json={
            "desc": "写字楼前的街道",
            "scene": "style",
            "style": "国风水墨",
            "modify": "画面里加一把红伞",
        },
    )
    result = next(e for e in parse_events(resp.text) if e["event"] == "result")["data"]
    assert "红伞" in result["prompt"]
    assert any(n["rule"] == "i2i_modify_ref" for n in result["notes"])


async def test_i2i_template_ignored_outside_modify(client):
    """修改模板是精准修改专属：其他场景即使传了 template 也不生效。"""
    resp = await client.post(
        "/api/i2i-generations",
        json={
            "desc": "一只猫趴在窗台上",
            "scene": "creative",
            "template": "portrait",
            "modify": "对人像进行精修",
        },
    )
    result = next(e for e in parse_events(resp.text) if e["event"] == "result")["data"]
    assert not any(w["rule"] == "i2i_portrait_no_person" for w in result["warnings"])
    # 修改意向仍然通用生效
    assert all("对人像进行精修" in p["prompt"] for p in result["prompts"])


async def test_i2i_style_scene(client):
    resp = await client.post(
        "/api/i2i-generations",
        json={
            "desc": "写字楼前的街道",
            "scene": "style",
            "style": "国风水墨",
        },
    )
    result = next(e for e in parse_events(resp.text) if e["event"] == "result")["data"]
    assert len(result["prompts"]) == 1
    assert "国风水墨" in result["prompt"]
    assert "保留原图的构图、主体与空间关系" in result["prompt"]


async def test_i2i_outpaint_default_ratio(client):
    """扩图模板未指定画幅 → 默认 2.35:1 并写入提示词与说明。"""
    resp = await client.post(
        "/api/i2i-generations",
        json={
            "desc": "一片湖水与远山",
            "scene": "modify",
            "modify": "以原图为中心向外延展画面，适配目标画幅",
            "template": "outpaint",
        },
    )
    result = next(e for e in parse_events(resp.text) if e["event"] == "result")["data"]
    assert result["suggested_ratio"] == "2.35:1"
    assert "画幅比例 2.35:1" in result["prompt"]
    assert any(n["rule"] == "i2i_outpaint_ratio" for n in result["notes"])


async def test_i2i_portrait_no_person_warning(client):
    """人像精修但描述无人物 → 警告。"""
    resp = await client.post(
        "/api/i2i-generations",
        json={
            "desc": "一只猫趴在窗台上",
            "scene": "modify",
            "template": "portrait",
            "modify": "对人像进行精修",
        },
    )
    result = next(e for e in parse_events(resp.text) if e["event"] == "result")["data"]
    assert any(w["rule"] == "i2i_portrait_no_person" for w in result["warnings"])


async def test_i2i_empty_desc_rejected(client):
    """图片描述必填（PRD v0.2 M8）。"""
    resp = await client.post("/api/i2i-generations", json={"desc": "", "scene": "modify"})
    assert resp.status_code == 422
