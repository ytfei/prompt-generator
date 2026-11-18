import json

from app.agent.graph import NODES


async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_options_shape(client):
    resp = await client.get("/api/options")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["groups"]) == 14
    assert "usage" in data["groups"]
    assert len(data["presets"]) == 13
    # 财经行情首图预设带分类与主题提示语
    fin = [p for p in data["presets"] if p.get("category") == "财经行情首图"]
    assert len(fin) == 10
    assert all(p.get("theme_hint") for p in fin)
    assert all(p["selections"]["usage"] == "公众号首图" for p in fin)


async def test_generation_sse_flow_and_persist(client):
    resp = await client.post(
        "/api/generations",
        json={"selections": {"style": "电影感", "usage": "文章配图"}, "theme": "深夜书房"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    events = []
    for block in resp.text.split("\n\n"):
        if not block.strip():
            continue
        ev = {}
        for line in block.splitlines():
            if line.startswith("event: "):
                ev["event"] = line[7:]
            elif line.startswith("data: "):
                ev["data"] = json.loads(line[6:])
        events.append(ev)

    steps = [e for e in events if e["event"] == "step"]
    done_nodes = [s["data"]["node"] for s in steps if s["data"]["status"] == "done"]
    assert done_nodes == NODES
    result = next(e for e in events if e["event"] == "result")
    assert "电影级画面质感" in result["data"]["prompt"]
    assert result["data"]["id"]

    # 已落库，可查询
    lst = await client.get("/api/generations")
    assert lst.status_code == 200
    items = lst.json()
    assert any(it["id"] == result["data"]["id"] for it in items)
    assert items[0]["final_prompt"]  # 按时间倒序，最新一条在前


async def test_favorite_toggle_and_delete(client):
    resp = await client.post(
        "/api/generations", json={"selections": {}, "theme": "测试"}
    )
    result = None
    for b in resp.text.split("\n\n"):
        for line in b.splitlines():
            if line.startswith("data: ") and '"prompt"' in line:
                result = json.loads(line[6:])
                break
        if result:
            break
    assert result is not None
    gen_id = result["id"]

    patched = await client.patch(f"/api/generations/{gen_id}", json={"favorite": True})
    assert patched.json()["favorite"] is True

    favs = await client.get("/api/generations", params={"favorite": True})
    assert len(favs.json()) == 1

    deleted = await client.delete(f"/api/generations/{gen_id}")
    assert deleted.json()["ok"] is True
    assert (await client.get(f"/api/generations/{gen_id}")).status_code == 404


async def test_template_crud(client):
    created = await client.post(
        "/api/templates",
        json={"name": "我的模板", "selections": {"style": "油画"}},
    )
    assert created.status_code == 200
    tpl_id = created.json()["id"]

    listed = await client.get("/api/templates")
    assert [t["id"] for t in listed.json()] == [tpl_id]

    assert (await client.delete(f"/api/templates/{tpl_id}")).json()["ok"] is True
    assert (await client.get("/api/templates")).json() == []
