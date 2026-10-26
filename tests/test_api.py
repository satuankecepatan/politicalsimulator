from fastapi.testclient import TestClient
from polsim.api.app import app

client = TestClient(app)


def test_schema_endpoint():
    res = client.get("/api/schema")
    assert res.status_code == 200
    data = res.json()
    assert "properties" in data
    assert "axes" in data["properties"]


def test_presets_endpoints():
    res = client.get("/api/presets")
    assert res.status_code == 200
    presets = res.json()
    assert "industrial_democracy" in presets

    res_single = client.get("/api/presets/industrial_democracy")
    assert res_single.status_code == 200
    cfg = res_single.json()
    assert "name" in cfg
    assert len(cfg["parties"]) >= 3


def test_session_lifecycle():
    # 1. Create session
    create_res = client.post("/api/sessions", json={"preset": "industrial_democracy", "seed": 42})
    assert create_res.status_code == 200
    data = create_res.json()
    sid = data["session_id"]
    assert sid is not None
    assert "map" in data
    assert "compass" in data

    # 2. Get status
    stat_res = client.get(f"/api/sessions/{sid}")
    assert stat_res.status_code == 200
    stat = stat_res.json()
    assert stat["tick"] == 0

    # 3. Tick 1 month
    tick_res = client.post(f"/api/sessions/{sid}/tick")
    assert tick_res.status_code == 200
    tick_data = tick_res.json()
    assert tick_data["summary"]["tick"] == 1

    # 4. Intervene by triggering an event
    int_res = client.post(
        f"/api/sessions/{sid}/intervene",
        json={"type": "event", "event_id": "econ_mineral_boom"},
    )
    assert int_res.status_code == 200

    # 5. Export Markdown
    exp_res = client.get(f"/api/sessions/{sid}/export/markdown")
    assert exp_res.status_code == 200
    assert "text/markdown" in exp_res.headers["content-type"]
    assert len(exp_res.text) > 50

    # 6. Save to SQLite
    save_res = client.post(f"/api/sessions/{sid}/save")
    assert save_res.status_code == 200
    assert save_res.json()["status"] == "saved"
