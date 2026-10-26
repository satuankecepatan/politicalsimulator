import numpy as np
from polsim.config.presets import build_scenario
from polsim.core.rng import RngStreams
from polsim.population.drift import step_demographic_drift
from polsim.population.generator import generate_cohorts
from polsim.territory.regions import apportion_seats, generate_territory


def test_seat_apportionment():
    pops = [100.0, 200.0, 300.0, 400.0]
    total_seats = 100
    allocated = apportion_seats(pops, total_seats, min_seats=1)
    assert sum(allocated) == total_seats
    assert allocated == [10, 20, 30, 40]


def test_territory_generation():
    sc = build_scenario("industrial_democracy", seed=42)
    rng = RngStreams(seed=42)
    territory, map_data = generate_territory(sc.country, sc.institutions, rng["territory"])

    assert len(territory.regions) == sc.country.n_regions
    total_allocated_seats = sum(r.seats for r in territory.regions.values())
    assert total_allocated_seats == sc.institutions.seats
    assert territory.graph.number_of_nodes() == sc.country.n_regions
    assert len(map_data["features"]) == sc.country.n_regions


def test_cohort_generation_and_drift():
    sc = build_scenario("industrial_democracy", seed=100)
    rng = RngStreams(seed=100)
    territory, _ = generate_territory(sc.country, sc.institutions, rng["territory"])
    cohorts = generate_cohorts(sc, territory, rng["demographics"])

    # Verify cohort counts and properties
    assert cohorts.n_cohorts == sc.country.n_regions * sc.demographics.cohorts_per_region
    assert np.all(cohorts.sizes > 0)
    assert np.isclose(np.sum(cohorts.sizes), sc.country.population, rtol=1e-3)
    assert np.all(cohorts.positions >= -1.0) and np.all(cohorts.positions <= 1.0)
    assert np.all(cohorts.salience >= 0.0) and np.all(cohorts.salience <= 1.0)
    assert np.all(cohorts.turnout >= 0.0) and np.all(cohorts.turnout <= 1.0)

    # Test demographic drift conservation of total population
    initial_pop = np.sum(cohorts.sizes)
    step_demographic_drift(cohorts, dt_months=12.0, rng=rng["demographics"])
    post_pop = np.sum(cohorts.sizes)
    assert np.isclose(initial_pop, post_pop)
