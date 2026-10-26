import numpy as np
from polsim.config.presets import build_scenario
from polsim.config.schema import CordonRule, GovernmentParams, PartyParams
from polsim.core.rng import RngStreams
from polsim.engine.state import FactionState, PartyState
from polsim.parties.ai import adapt_parties
from polsim.parties.coalition import form_coalition
from polsim.parties.lifecycle import step_party_lifecycle
from polsim.parties.relations import initialize_relations, update_relations
from polsim.population.generator import generate_cohorts
from polsim.territory.regions import generate_territory


def test_relations_and_cordon_sanitaire():
    p1 = PartyState(
        id="p1", name="Party 1", abbreviation="P1", color="#000",
        position=np.array([0.0, 0.0]), salience=np.array([1.0, 1.0]),
    )
    p2 = PartyState(
        id="p2", name="Party 2", abbreviation="P2", color="#FFF",
        position=np.array([0.85, 0.0]), salience=np.array([1.0, 1.0]),
    )
    cordon = [CordonRule(axis="economic", beyond=75.0)]
    rel = initialize_relations([p1, p2], axes=["economic", "social"], cordon_rules=cordon)

    # Party 2 position on economic axis is 0.85 > 0.75, so cordon applies
    assert rel.trust[0, 1] == 0.0
    assert rel.hostility[0, 1] >= 0.85


def test_party_repositioning():
    sc = build_scenario("industrial_democracy", seed=12)
    rng = RngStreams(seed=12)
    territory, _ = generate_territory(sc.country, sc.institutions, rng["territory"])
    cohorts = generate_cohorts(sc, territory, rng["demographics"])

    parties = [
        PartyState(
            id=p.id, name=p.name, abbreviation=p.abbreviation, color=p.color,
            position=np.array([p.ideology.get(a, 0.0) / 100.0 for a in sc.axis_ids]),
            salience=np.array([p.salience.get(a, 0.5) for a in sc.axis_ids]),
            pragmatism=0.6,
        )
        for p in sc.parties
    ]
    rel = initialize_relations(parties, axes=sc.axis_ids, cordon_rules=[])

    initial_pos = parties[0].position.copy()
    adapt_parties(parties, cohorts, rel, sc.parameters.parties, tick=3, rng=rng["party_ai"])
    new_pos = parties[0].position

    # Party moved within bounded step size
    step_taken = float(np.linalg.norm(new_pos - initial_pos))
    assert step_taken > 0.0
    assert step_taken <= (sc.parameters.parties.max_step * 0.6) + 1e-6


def test_coalition_formation():
    p1 = PartyState(id="p1", name="P1", abbreviation="P1", color="#F00", position=np.array([-0.2]), salience=np.array([1.0]), seats=40)
    p2 = PartyState(id="p2", name="P2", abbreviation="P2", color="#0F0", position=np.array([-0.1]), salience=np.array([1.0]), seats=20)
    p3 = PartyState(id="p3", name="P3", abbreviation="P3", color="#00F", position=np.array([0.7]), salience=np.array([1.0]), seats=40)
    parties = [p1, p2, p3]

    rel = initialize_relations(parties, axes=["economic"], cordon_rules=[])
    gov = form_coalition(parties, rel, total_parliament_seats=100, params=GovernmentParams())

    # p1 (40) + p2 (20) = 60 seats (> 50 majority) and ideologically adjacent
    assert gov.leader_party_id == "p1"
    assert "p1" in gov.coalition_party_ids
    assert "p2" in gov.coalition_party_ids
    assert "p3" not in gov.coalition_party_ids
    assert p1.in_government and p2.in_government and not p3.in_government


def test_party_split_on_low_cohesion():
    p1 = PartyState(
        id="split_p", name="Big Party", abbreviation="BP", color="#111",
        position=np.array([0.0, 0.0]), salience=np.array([1.0, 1.0]),
        cohesion=0.10,  # Below split cohesion threshold
        factions=[
            FactionState(name="Radical Wing", offset=np.array([0.5, 0.5]), weight=0.4),
            FactionState(name="Moderate Core", offset=np.array([0.0, 0.0]), weight=0.6),
        ],
    )
    parties = [p1]
    rel = initialize_relations(parties, axes=["economic", "social"], cordon_rules=[])
    rng = np.random.default_rng(999)

    class DummyCohorts:
        positions = np.zeros((2, 2))
        salience = np.zeros((2, 2))

    params = PartyParams(split_hazard=1.0, split_cohesion=0.30)
    changed, logs = step_party_lifecycle(parties, rel, DummyCohorts(), params, tick=1, rng=rng)

    assert changed is True
    assert len(parties) == 2
    assert "Radical Wing" in parties[1].name
