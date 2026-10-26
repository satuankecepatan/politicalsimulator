"""Calibration harness for running parallel seeded simulations and validating against real-world metrics."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import Any
import numpy as np
import pandas as pd

from polsim.analytics.metrics import effective_number_of_parties, gallagher_index
from polsim.config.presets import build_scenario
from polsim.config.schema import ScenarioConfig
from polsim.engine.simulation import Simulation


@dataclass(slots=True)
class SimulationMetricsResult:
    seed: int
    mean_turnout: float
    mean_enp: float
    mean_gallagher: float
    total_elections: int
    total_splits: int
    total_mergers: int
    duration_ticks: int


def _run_single_seed(args: tuple[dict[str, Any], int, int]) -> SimulationMetricsResult:
    config_dict, seed, years = args
    sc = ScenarioConfig.model_validate(config_dict)
    sc.settings.seed = seed
    sim = Simulation(sc)
    sim.run(years=years)

    elections = sim.history.filter(entry_type="election")
    turnouts = [e.details.get("turnout", 0.0) for e in elections if "turnout" in e.details]
    enps: list[float] = []
    gallaghers: list[float] = []

    for e in elections:
        shares = list(e.details.get("shares", {}).values())
        seats = list(e.details.get("seats", {}).values())
        if shares:
            enps.append(effective_number_of_parties(shares))
        if shares and seats and sum(seats) > 0:
            seat_shares = [s / sum(seats) for s in seats]
            gallaghers.append(gallagher_index(shares, seat_shares))

    splits = len(sim.history.filter(entry_type="split"))
    mergers = len(sim.history.filter(entry_type="merger"))

    return SimulationMetricsResult(
        seed=seed,
        mean_turnout=float(np.mean(turnouts)) if turnouts else 0.0,
        mean_enp=float(np.mean(enps)) if enps else 0.0,
        mean_gallagher=float(np.mean(gallaghers)) if gallaghers else 0.0,
        total_elections=len(elections),
        total_splits=splits,
        total_mergers=mergers,
        duration_ticks=sim.state.tick,
    )


class CalibrationHarness:
    """Runs batch seeded simulations in parallel and checks against documented empirical ranges."""

    # Documented real-world ranges
    EMPIRICAL_RANGES = {
        "turnout_min": 0.45,
        "turnout_max": 0.90,
        "enp_pr_min": 2.2,
        "enp_pr_max": 7.0,
        "enp_fptp_min": 1.7,
        "enp_fptp_max": 3.8,
        "gallagher_pr_max": 10.0,
    }

    def __init__(self, base_config: ScenarioConfig | None = None):
        self.config = base_config or build_scenario("industrial_democracy")

    def run_batch(
        self,
        n_runs: int = 10,
        years: int = 20,
        start_seed: int = 1000,
        max_workers: int = 4,
    ) -> pd.DataFrame:
        """Run parallel seeded simulations and aggregate metrics into a pandas DataFrame."""
        cfg_dict = self.config.model_dump(mode="json")
        seeds = [start_seed + i for i in range(n_runs)]
        task_args = [(cfg_dict, s, years) for s in seeds]

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(_run_single_seed, task_args))

        rows = [
            {
                "seed": r.seed,
                "turnout": r.mean_turnout,
                "enp": r.mean_enp,
                "gallagher": r.mean_gallagher,
                "elections": r.total_elections,
                "splits": r.total_splits,
                "mergers": r.total_mergers,
            }
            for r in results
        ]
        df = pd.DataFrame(rows)
        return df

    def evaluate_calibration(self, df: pd.DataFrame) -> dict[str, Any]:
        """Check report against empirical bounds and flag out-of-range indicators."""
        mean_turnout = float(df["turnout"].mean())
        mean_enp = float(df["enp"].mean())
        mean_gallagher = float(df["gallagher"].mean())

        flags: list[str] = []
        if mean_turnout < self.EMPIRICAL_RANGES["turnout_min"]:
            flags.append(f"Turnout ({mean_turnout:.1%}) below empirical minimum (45%).")
        elif mean_turnout > self.EMPIRICAL_RANGES["turnout_max"]:
            flags.append(f"Turnout ({mean_turnout:.1%}) above empirical maximum (90%).")

        is_pr = self.config.institutions.electoral_system == "pr"
        if is_pr and mean_enp < self.EMPIRICAL_RANGES["enp_pr_min"]:
            flags.append(f"PR Effective Number of Parties ({mean_enp:.2f}) below expected minimum (2.2).")
        if is_pr and mean_gallagher > self.EMPIRICAL_RANGES["gallagher_pr_max"]:
            flags.append(f"PR Gallagher Index ({mean_gallagher:.2f}) shows excessive disproportionality.")

        return {
            "mean_turnout": round(mean_turnout, 3),
            "mean_enp": round(mean_enp, 2),
            "mean_gallagher": round(mean_gallagher, 2),
            "flags": flags,
            "calibrated": len(flags) == 0,
        }
