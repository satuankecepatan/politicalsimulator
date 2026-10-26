import pytest
from polsim.config.schema import EventSettings
from polsim.core.calendar import SimDate
from polsim.engine.state import EconomyState, GovernmentState, PartyState, SimState
from polsim.events.engine import EventEngine
from polsim.events.expr import evaluate_precondition


def test_safe_precondition_evaluation():
    ctx = {
        "economy": {"growth": 2.5, "corruption": 0.45},
        "government": {"stability": 0.8},
        "tick": 24,
    }

    assert evaluate_precondition("economy.growth > 2.0 and economy.corruption >= 0.4", ctx) is True
    assert evaluate_precondition("economy.growth < 1.0", ctx) is False
    assert evaluate_precondition("government.stability > 0.5 or tick == 10", ctx) is True

    # Malicious or disallowed calls must return False safely
    assert evaluate_precondition("__import__('os').system('ls')", ctx) is False
    assert evaluate_precondition("eval('1+1')", ctx) is False


def test_events_library_loaded_and_valid():
    settings = EventSettings()
    engine = EventEngine(settings)
    assert len(engine.events) >= 50
    # Check diverse categories exist
    categories = {ev.category for ev in engine.events.values()}
    assert "economic" in categories
    assert "scandal" in categories
    assert "security" in categories
    assert "disaster" in categories


def test_event_application_and_expiration():
    settings = EventSettings()
    engine = EventEngine(settings)

    econ = EconomyState(growth=2.0)
    gov = GovernmentState()
    party = PartyState(
        id="gov_party", name="Gov Party", abbreviation="GP", color="#F00",
        position=None, salience=None, is_leader=True, scandal_accum=0.0,
    )
    state = SimState(
        tick=1,
        date=SimDate(2000, 1),
        axes=[],
        parties=[party],
        party_indices={"gov_party": 0},
        cohorts=None,
        territory=None,
        economy=econ,
        government=gov,
        relations=None,
    )

    # Manually pick scandal event
    scandal_event = engine.events["scn_offshore_leak"]
    initial_scandal = party.scandal_accum
    engine._apply_event(scandal_event, state)

    # Scandal accumulated on leader party
    assert party.scandal_accum > initial_scandal
    assert len(state.active_effects) > 0

    # Step with chaos = 0 so no new random events roll
    engine.settings.chaos_level = 0.0
    dur = state.active_effects[0].remaining_ticks
    for _ in range(dur):
        engine.step(state, rng=pytest.importorskip("numpy.random").default_rng())

    assert len(state.active_effects) == 0
