import numpy as np
from polsim.analytics.metrics import (
    dalton_polarization,
    effective_number_of_parties,
    gallagher_index,
    pedersen_volatility,
)
from polsim.config.presets import build_scenario
from polsim.core.rng import RngStreams
from polsim.engine.state import EconomyState, PartyState
from polsim.population.generator import generate_cohorts
from polsim.territory.regions import generate_territory
from polsim.voting.allocation import allocate_seats
from polsim.voting.elections import conduct_election
from polsim.voting.model import resolve_probabilistic_votes


def test_dhondt_textbook_example():
    """Textbook D'Hondt example: 8 seats, 4 parties."""
    votes = np.array([100_000, 80_000, 30_000, 20_000], dtype=np.float64)
    # A=100k, B=80k, C=30k, D=20k
    seats = allocate_seats(votes, total_seats=8, formula="dhondt", threshold=0.0)
    assert np.array_equal(seats, [4, 3, 1, 0])


def test_sainte_lague_allocation():
    votes = np.array([100_000, 80_000, 30_000, 20_000], dtype=np.float64)
    seats = allocate_seats(votes, total_seats=8, formula="sainte_lague", threshold=0.0)
    assert sum(seats) == 8


def test_largest_remainder_hare():
    votes = np.array([100_000, 80_000, 30_000, 20_000], dtype=np.float64)
    seats = allocate_seats(votes, total_seats=8, formula="largest_remainder", threshold=0.0)
    assert sum(seats) == 8


def test_enp_and_gallagher_metrics():
    # Two equal parties -> ENP = 2.0
    assert np.isclose(effective_number_of_parties([0.5, 0.5]), 2.0)
    # Four equal parties -> ENP = 4.0
    assert np.isclose(effective_number_of_parties([0.25, 0.25, 0.25, 0.25]), 4.0)

    # Perfect proportionality -> Gallagher = 0.0
    assert np.isclose(gallagher_index([0.4, 0.6], [0.4, 0.6]), 0.0)

    # Pedersen volatility
    past = {"A": 0.40, "B": 0.60}
    curr = {"A": 0.50, "B": 0.50}
    assert np.isclose(pedersen_volatility(past, curr), 10.0)


def test_full_election_execution():
    sc = build_scenario("industrial_democracy", seed=777)
    rng = RngStreams(seed=777)
    territory, _ = generate_territory(sc.country, sc.institutions, rng["territory"])
    cohorts = generate_cohorts(sc, territory, rng["demographics"])

    # Build PartyStates from config
    parties = [
        PartyState(
            id=p.id,
            name=p.name,
            abbreviation=p.abbreviation,
            color=p.color,
            position=np.array([p.ideology.get(a, 0.0) / 100.0 for a in sc.axis_ids]),
            salience=np.array([p.salience.get(a, 0.5) for a in sc.axis_ids]),
            pragmatism=p.pragmatism,
            organization=p.organization,
            funding=p.funding,
            charisma=p.charisma,
            cohesion=p.cohesion,
            populism=p.populism,
            corruption=p.corruption,
            coalition_willingness=p.coalition_willingness,
            base_appeal=p.base_appeal,
        )
        for p in sc.parties
    ]

    econ = EconomyState()

    # Test PR Election
    res_pr = conduct_election(
        tick=48,
        cohorts=cohorts,
        parties=parties,
        territory=territory,
        economy=econ,
        institutions=sc.institutions,
        voting_params=sc.parameters.voting,
        rng=rng["elections"],
    )
    assert res_pr.total_seats == sc.institutions.seats
    assert sum(res_pr.party_seats.values()) == sc.institutions.seats
    assert res_pr.turnout > 0.40 and res_pr.turnout < 0.95
    assert len(res_pr.regional_results) == sc.country.n_regions
