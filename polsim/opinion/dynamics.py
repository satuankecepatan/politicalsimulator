"""Public opinion dynamics: thermostatic shifts, economic hardship, persuasion, and causality tracing."""

from __future__ import annotations

import numpy as np

from polsim.config.schema import OpinionParams
from polsim.core.mathx import clamp
from polsim.engine.state import CohortState, EconomyState, PartyState


def step_opinion_dynamics(
    cohorts: CohortState,
    parties: list[PartyState],
    economy: EconomyState,
    params: OpinionParams,
    dt_months: float,
    rng: np.random.Generator,
) -> dict[str, float]:
    """Step cohort ideological positions and salience, tracking contributing deltas.

    Returns:
        Dictionary of national average ideological shifts broken down by cause.
    """
    n_cohorts = cohorts.n_cohorts
    n_dim = cohorts.positions.shape[1]
    m_parties = len(parties)

    causes_delta: dict[str, float] = {
        "thermostatic": 0.0,
        "hardship": 0.0,
        "baseline_reversion": 0.0,
        "persuasion": 0.0,
    }

    # 1. Baseline Reversion: slow pull toward demographic structural baseline
    reversion_shift = params.baseline_reversion * (cohorts.baselines - cohorts.positions) * dt_months
    cohorts.positions += reversion_shift
    causes_delta["baseline_reversion"] = float(np.mean(np.abs(reversion_shift)))

    # 2. Thermostatic Public Opinion:
    # Public opinion reacts opposite to governing coalition policy stance
    governing = [p for p in parties if p.in_government and p.active]
    if governing:
        gov_stance = np.mean([p.position for p in governing], axis=0)  # (D,)
        # Counter-reaction in the opposite direction
        thermo_shift = -params.thermostatic_rate * gov_stance[None, :] * dt_months
        cohorts.positions += thermo_shift
        causes_delta["thermostatic"] = float(np.mean(np.abs(thermo_shift)))

    # 3. Material Hardship Shift:
    # High unemployment and inflation increase demand for economic support (negative on economic axis)
    if economy.unemployment > 6.5 or economy.inflation > 3.0:
        hardship_scale = (
            max(0.0, economy.unemployment - 6.5) * 0.1
            + max(0.0, economy.inflation - 3.0) * 0.1
        )
        hardship_shift = np.zeros_like(cohorts.positions)
        hardship_shift[:, 0] = -params.hardship_left_shift * hardship_scale * dt_months
        cohorts.positions += hardship_shift
        causes_delta["hardship"] = float(np.mean(np.abs(hardship_shift)))

    # 4. Cue-taking / Persuasion from Supported Parties:
    # Loyal voters drift slightly toward their party's position
    if m_parties > 0:
        party_positions = np.array([p.position for p in parties])  # (M, D)
        # Weight by cohort loyalty
        loyalty_weights = cohorts.loyalty[:, :m_parties]  # (N, M)
        sum_loyalty = np.sum(loyalty_weights, axis=1, keepdims=True)  # (N, 1)
        sum_loyalty = np.where(sum_loyalty == 0, 1.0, sum_loyalty)
        norm_loyalty = loyalty_weights / sum_loyalty

        favored_positions = np.dot(norm_loyalty, party_positions)  # (N, D)
        cue_shift = params.persuasion_rate * (favored_positions - cohorts.positions) * dt_months
        cohorts.positions += cue_shift
        causes_delta["persuasion"] = float(np.mean(np.abs(cue_shift)))

    # 5. Stochastic Ideological Diffusion
    noise = rng.normal(0.0, params.noise * np.sqrt(dt_months), size=cohorts.positions.shape)
    cohorts.positions = clamp(cohorts.positions + noise, -1.0, 1.0)

    # 6. Salience Mean-Reversion toward baseline
    salience_drift = params.salience_reversion * (0.5 - cohorts.salience) * (dt_months / 12.0)
    cohorts.salience = clamp(cohorts.salience + salience_drift, 0.1, 1.0)

    # 7. Natural Partisan Loyalty Decay
    loyalty_decay = (1.0 - params.loyalty_decay * dt_months)
    cohorts.loyalty = clamp(cohorts.loyalty * loyalty_decay, 0.0, 0.95)

    return causes_delta
