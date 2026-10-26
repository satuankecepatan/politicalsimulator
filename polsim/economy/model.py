"""Macroeconomic stochastic model using Ornstein-Uhlenbeck processes."""

from __future__ import annotations

import numpy as np

from polsim.config.schema import EconomyParams
from polsim.core.mathx import ornstein_uhlenbeck_step
from polsim.engine.state import EconomyState, PartyState


def step_economy(
    economy: EconomyState,
    governing_parties: list[PartyState],
    params: EconomyParams,
    dt_months: float,
    rng: np.random.Generator,
) -> None:
    """Step macroeconomic indicators with mean-reversion and policy equilibrium adjustments.

    Symmetric modeling: Left-leaning policies increase social security / lower inequality
    at the cost of marginal growth; right-leaning policies increase growth at the cost of higher inequality.
    Neither is privileged.
    """
    dt = dt_months / 12.0  # Annualized time step

    # Calculate government economic stance in [-1, 1]
    if governing_parties:
        gov_econ_pos = float(np.mean([p.position[0] for p in governing_parties]))
    else:
        gov_econ_pos = 0.0

    # Policy shifts long-run equilibrium points
    # Free-market (+): higher growth equilibrium (+0.5%), higher inequality (+0.02)
    # State-led (-): lower inequality (-0.02), slightly lower growth (-0.5%)
    target_growth_mu = params.growth_mu + (params.policy_effect * gov_econ_pos * 0.6)
    target_inequality_mu = params.inequality_mu + (0.03 * gov_econ_pos)

    # 1. Real GDP Growth
    economy.growth = ornstein_uhlenbeck_step(
        x=economy.growth,
        mu=target_growth_mu,
        theta=params.growth_theta,
        sigma=params.growth_sigma,
        dt=dt,
        rng=rng,
    )

    # 2. CPI Inflation
    economy.inflation = ornstein_uhlenbeck_step(
        x=economy.inflation,
        mu=params.inflation_mu,
        theta=params.inflation_theta,
        sigma=params.inflation_sigma,
        dt=dt,
        rng=rng,
    )

    # 3. Unemployment (Okun's law linkage to GDP growth gap)
    growth_gap = economy.growth - target_growth_mu
    unemp_target = params.unemployment_mu - (params.okun * growth_gap * 10.0)
    economy.unemployment = ornstein_uhlenbeck_step(
        x=economy.unemployment,
        mu=unemp_target,
        theta=params.unemployment_theta,
        sigma=0.3,
        dt=dt,
        rng=rng,
    )

    # 4. Gini Inequality
    economy.inequality = ornstein_uhlenbeck_step(
        x=economy.inequality,
        mu=target_inequality_mu,
        theta=params.inequality_theta,
        sigma=params.inequality_sigma,
        dt=dt,
        rng=rng,
    )

    # 5. Security & Stability
    economy.security = float(
        np.clip(
            ornstein_uhlenbeck_step(
                x=economy.security,
                mu=0.85,
                theta=params.security_theta,
                sigma=0.04,
                dt=dt,
                rng=rng,
            ),
            0.1,
            0.98,
        )
    )

    # 6. Perceived Corruption
    economy.corruption = float(
        np.clip(
            ornstein_uhlenbeck_step(
                x=economy.corruption,
                mu=0.25,
                theta=params.corruption_theta,
                sigma=0.03,
                dt=dt,
                rng=rng,
            ),
            0.02,
            0.95,
        )
    )
