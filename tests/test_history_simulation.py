import hashlib
import json
import pytest
from polsim.config.presets import build_scenario
from polsim.engine.simulation import Simulation
from polsim.history.export import export_markdown_chronicle
from polsim.history.store import HistoryStore


def test_simulation_10_years():
    sc = build_scenario("industrial_democracy", seed=42)
    sc.country.n_regions = 6
    sc.demographics.cohorts_per_region = 4
    sim = Simulation(sc)

    # Initial state has 1 election to establish starting parliament
    assert len(sim.history.entries) >= 2
    assert sim.state.government.leader_party_id is not None

    # Run for 10 years (120 ticks)
    sim.run(years=10)
    assert sim.state.tick == 120
    assert sim.state.date.year == sc.country.start_year + 10

    # Ensure multiple elections and coalition formations occurred
    elections = sim.history.filter(entry_type="election")
    assert len(elections) >= 3  # Initial + 2 regular 4-year cycle elections

    # Check status summary and compass preview
    status = sim.get_status_summary()
    assert status["tick"] == 120
    assert "economy" in status
    assert len(status["parties"]) >= 3

    compass = sim.get_compass_preview()
    assert "cohorts" in compass
    assert len(compass["cohorts"]) == 24
    assert len(compass["parties"]) >= 3


def test_deterministic_history_reproducibility():
    """Identical seed and config must produce an identical history hash."""
    sc1 = build_scenario("industrial_democracy", seed=9876)
    sc1.country.n_regions = 5
    sc1.demographics.cohorts_per_region = 3

    sim1 = Simulation(sc1)
    sim1.run(years=5)
    records1 = [e.to_dict() for e in sim1.history.entries]
    hash1 = hashlib.sha256(json.dumps(records1, sort_keys=True, default=lambda o: o.item() if hasattr(o, "item") else str(o)).encode("utf-8")).hexdigest()

    sc2 = build_scenario("industrial_democracy", seed=9876)
    sc2.country.n_regions = 5
    sc2.demographics.cohorts_per_region = 3

    sim2 = Simulation(sc2)
    sim2.run(years=5)
    records2 = [e.to_dict() for e in sim2.history.entries]
    hash2 = hashlib.sha256(json.dumps(records2, sort_keys=True, default=lambda o: o.item() if hasattr(o, "item") else str(o)).encode("utf-8")).hexdigest()

    assert hash1 == hash2


def test_sqlite_store_and_chronicle(tmp_path):
    sc = build_scenario("industrial_democracy", seed=55)
    sim = Simulation(sc)
    sim.run(years=4)

    # Test Markdown Chronicle
    chronicle = export_markdown_chronicle(sim.history)
    assert "# Historical Political Chronicle" in chronicle
    assert "General Election" in chronicle

    # Test SQLite Store
    db_file = tmp_path / "test_store.db"
    store = HistoryStore(db_file)
    store.save_run(
        run_id="run_001",
        config=sc,
        history=sim.history,
        snapshot_bytes=sim.snapshot(),
        tick=sim.state.tick,
    )

    runs = store.list_runs()
    assert len(runs) == 1
    assert runs[0]["id"] == "run_001"

    loaded_cfg, loaded_history = store.load_run("run_001")
    assert loaded_cfg.name == sc.name
    assert len(loaded_history.entries) == len(sim.history.entries)


def test_snapshot_restore_and_forking():
    sc = build_scenario("industrial_democracy", seed=77)
    sim = Simulation(sc)
    sim.run(years=3)

    # Capture snapshot
    snap_bytes = sim.snapshot()
    from polsim.engine.snapshot import restore_snapshot

    restored_sim = restore_snapshot(snap_bytes)
    assert restored_sim.state.tick == sim.state.tick
    assert restored_sim.state.date == sim.state.date

    # Fork timeline with new seed
    forked = sim.fork(new_seed=999)
    assert forked.state.tick == sim.state.tick
    # Stepping both should work without error
    sim.tick()
    forked.tick()
    assert sim.state.tick == 37
    assert forked.state.tick == 37
