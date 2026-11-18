import json

from app.agent.prompt_loader import load_prompt


async def _create_generation(client, selections=None, theme="测试主题"):
    resp = await client.post(
        "/api/generations", json={"selections": selections or {}, "theme": theme}
    )
    for b in resp.text.split("\n\n"):
        for line in b.splitlines():
            if line.startswith("data: ") and '"prompt"' in line:
                return json.loads(line[6:])
    raise AssertionError("no result event: " + resp.text)


def _parse_events(text: str) -> list[dict]:
    events = []
    for block in text.split("\n\n"):
        ev = {}
        for line in block.splitlines():
            if line.startswith("event: "):
                ev["event"] = line[7:]
            elif line.startswith("data: "):
                ev["data"] = json.loads(line[6:])
        if ev:
            events.append(ev)
    return events


async def test_refine_creates_new_row_with_parent(client):
    base = await _create_generation(client, {"style": "电影感"}, "雨夜便利店")
    refine_resp = await client.post(
        f"/api/generations/{base['id']}/refine",
        json={"instruction": "画面更亮一些，减少阴影"},
    )
    assert refine_resp.status_code == 200
    events = _parse_events(refine_resp.text)
    done_nodes = [e["data"]["node"] for e in events if e["event"] == "step" and e["data"]["status"] == "done"]
    assert done_nodes == ["apply_instruction", "conflict_scan"]

    result = next(e for e in events if e["event"] == "result")["data"]
    assert result["parent_id"] == base["id"]
    assert "更亮" in result["prompt"]  # mock 模式：追加调整要求

    detail = await client.get(f"/api/generations/{result['id']}")
    assert detail.json()["mode"] == "refine"
    assert detail.json()["parent_id"] == base["id"]


async def test_refine_chain_keeps_thread_state(client):
    base = await _create_generation(client, {}, "测试")
    first = await client.post(
        f"/api/generations/{base['id']}/refine", json={"instruction": "要求A"}
    )
    second_base = next(
        e["data"] for e in _parse_events(first.text) if e["event"] == "result"
    )
    # 对迭代产物继续迭代：状态延续（mock 下两条要求都应可见）
    second = await client.post(
        f"/api/generations/{second_base['id']}/refine", json={"instruction": "要求B"}
    )
    result = next(e["data"] for e in _parse_events(second.text) if e["event"] == "result")
    assert "要求A" in result["prompt"] and "要求B" in result["prompt"]


async def test_feedback_upsert_and_query(client):
    base = await _create_generation(client)
    gen_id = base["id"]

    ok = await client.post(f"/api/generations/{gen_id}/feedback", json={"rating": 1})
    assert ok.json()["rating"] == 1
    assert (await client.get(f"/api/generations/{gen_id}")).json()["rating"] == 1

    # 覆盖式更新
    await client.post(f"/api/generations/{gen_id}/feedback", json={"rating": -1, "comment": "太暗"})
    detail = (await client.get(f"/api/generations/{gen_id}")).json()
    assert detail["rating"] == -1

    listed = await client.get("/api/generations")
    assert next(i for i in listed.json() if i["id"] == gen_id)["rating"] == -1

    bad = await client.post(f"/api/generations/{gen_id}/feedback", json={"rating": 5})
    assert bad.status_code == 422


def test_prompt_loader_renders_variables():
    rendered = load_prompt("refine", draft="测试草稿XYZ")
    assert "测试草稿XYZ" in rendered
    assert "${" not in rendered


def test_prompts_exist_for_all_llm_nodes():
    import app.agent.graph  # noqa: F401 确保图可导入
    for name in ["parse_intent", "enrich_details", "refine", "refine_instruction"]:
        assert load_prompt(name).strip()
