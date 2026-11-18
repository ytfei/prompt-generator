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


async def test_inspire_theme(client):
    resp = await client.post(
        "/api/inspire-theme",
        json={"selections": {"style": "超现实主义", "mood": "忧郁孤独"}},
    )
    assert resp.status_code == 200
    themes = resp.json()["themes"]
    assert len(themes) == 4
    assert all(t.strip() for t in themes)
    assert len(set(themes)) == 4  # 候选之间不重复


async def test_inspire_with_tier(client):
    resp = await client.post(
        "/api/inspire-theme",
        json={"selections": {}, "model_tier": "nano"},  # 未配置 nano → 回落默认
    )
    assert resp.status_code == 200
    assert len(resp.json()["themes"]) == 4


def test_model_tier_fallback():
    """档位回退逻辑：显式构造 Settings，不依赖本机 .env 内容。"""
    from app.core.config import Settings

    base = {"llm_model": "default-m", "llm_provider": "", "_env_file": None}
    # 未配置任何档位 → 一律回落默认
    s = Settings(**base, llm_model_nano="", llm_model_mid="", llm_model_pro="")
    assert s.model_for_tier("nano") == "default-m"
    assert s.model_for_tier("mid") == "default-m"
    assert s.model_for_tier("不存在的档位") == "default-m"
    assert s.tier_configured("nano") is False
    assert s.tier_configured("default") is True
    # 配置了 nano → nano 用快档，其余回落默认
    s2 = Settings(**base, llm_model_nano="nano-m")
    assert s2.model_for_tier("nano") == "nano-m"
    assert s2.model_for_tier("mid") == "default-m"
    assert s2.tier_configured("nano") is True


async def test_options_exposes_models(client):
    resp = await client.get("/api/options")
    models = resp.json()["models"]
    assert models["llm_enabled"] is False  # 测试环境为 mock
    assert models["tiers"] == []


def test_prompts_exist_for_all_llm_nodes():
    import app.agent.graph  # noqa: F401 确保图可导入
    for name in [
        "parse_intent", "enrich_details", "refine", "refine_instruction",
        "inspire_theme", "inspire_from_theme",
    ]:
        assert load_prompt(name).strip()
