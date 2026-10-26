"""Demographic drift and generational replacement (cohort-component transitions)."""

from __future__ import annotations

import numpy as np

from polsim.engine.state import CohortState


def step_demographic_drift(
    cohorts: CohortState,
    dt_months: float,
    rng: np.random.Generator,
    annual_urbanization_rate: float = 0.002,
    annual_education_gain: float = 0.0015,
) -> None:
    """Simulate slow demographic drift over time.

    Models:
    1. Generational replacement / aging: Slight population turnover.
    2. Urbanization: Gradual population transfer from rural to urban cohorts.
    3. Education expansion: Slight upward drift in higher-educated cohort weights.
    """
    years = dt_months / 12.0
    if years <= 0:
        return

    n = cohorts.n_cohorts
    if n <= 1:
        return

    # Identify rural vs urban cohorts
    rural_indices = [i for i, a in enumerate(cohorts.attrs) if a.get("settlement") == "rural"]
    urban_indices = [i for i, a in enumerate(cohorts.attrs) if a.get("settlement") == "urban"]

    if rural_indices and urban_indices:
        # Move tiny fraction of rural population to urban cohorts
        urban_shift_fraction = annual_urbanization_rate * years
        for r_idx in rural_indices:
            shift_amount = cohorts.sizes[r_idx] * urban_shift_fraction
            cohorts.sizes[r_idx] -= shift_amount
            # Distribute into a random urban cohort in the same region if possible
            r_region = cohorts.region_ids[r_idx]
            local_urbans = [u for u in urban_indices if cohorts.region_ids[u] == r_region]
            target_u = rng.choice(local_urbans) if local_urbans else rng.choice(urban_indices)
            cohorts.sizes[target_u] += shift_amount

    # Slight generational noise in baseline ideology
    noise = rng.normal(0.0, 0.0005 * np.sqrt(years), size=cohorts.baselines.shape)
    cohorts.baselines = np.clip(cohorts.baselines + noise, -1.0, 1.0)
