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


def test_party_customization_and_ideology_update():
    create_res = client.post("/api/sessions", json={"preset": "industrial_democracy", "seed": 42})
    assert create_res.status_code == 200
    sid = create_res.json()["session_id"]

    # Intervene to modify party name, abbr, color, and 7-axis ideology
    int_res = client.post(
        f"/api/sessions/{sid}/intervene",
        json={
            "type": "party_update",
            "party_id": "sdp",
            "name": "Progressive Vanguard Coalition",
            "abbreviation": "PVC",
            "color": "#00F0FF",
            "position": {
                "economic": -80.0,
                "social": -75.0,
                "authority": 10.0,
                "identity": -50.0,
                "secularism": -60.0,
                "environment": 90.0,
                "trust": -20.0,
            },
        },
    )
    assert int_res.status_code == 200
    stat = int_res.json()["summary"]
    parties = {p["id"]: p for p in stat["parties"]}
    assert "sdp" in parties
    sdp = parties["sdp"]
    assert sdp["name"] == "Progressive Vanguard Coalition"
    assert sdp["abbr"] == "PVC"
    assert sdp["color"] == "#00F0FF"
    assert sdp["ideology"]["economic"] == -80.0
    assert sdp["ideology"]["environment"] == 90.0


def test_create_session_with_custom_parties():
    custom_parties = [
        {
            "id": "tech_party",
            "name": "Technocratic Synthesists",
            "abbreviation": "TECH",
            "color": "#CCFF00",
            "ideology": {
                "economic": 20.0,
                "social": -40.0,
                "authority": 30.0,
                "identity": -10.0,
                "secularism": -80.0,
                "environment": 50.0,
                "trust": 70.0,
            },
        },
        {
            "id": "trad_union",
            "name": "Traditionalist Union",
            "abbreviation": "TU",
            "color": "#E63946",
            "ideology": {
                "economic": -60.0,
                "social": 60.0,
                "authority": 40.0,
                "identity": 50.0,
                "secularism": 40.0,
                "environment": -30.0,
                "trust": 10.0,
            },
        },
    ]

    create_res = client.post(
        "/api/sessions",
        json={
            "preset": "industrial_democracy",
            "seed": 101,
            "parties": custom_parties,
        },
    )
    assert create_res.status_code == 200
    data = create_res.json()
    summary = data["summary"]
    p_names = [p["name"] for p in summary["parties"]]
    assert "Technocratic Synthesists" in p_names
    assert "Traditionalist Union" in p_names
    assert len(summary["parties"]) == 2

