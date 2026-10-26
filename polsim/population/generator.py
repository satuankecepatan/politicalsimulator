"""Population demographic cohort generation and statistical initialization."""

from __future__ import annotations

import numpy as np

from polsim.config.schema import DemographicsConfig, PartyConfig, ScenarioConfig
from polsim.engine.state import CohortState, TerritoryState


def generate_cohorts(
    config: ScenarioConfig,
    territory: TerritoryState,
    rng: np.random.Generator,
) -> CohortState:
    """Generate demographic cohorts across regions using Dirichlet and MVN sampling."""
    demo_cfg = config.demographics
    axes = config.axis_ids
    n_dim = len(axes)
    axis_idx = {axis: i for i, axis in enumerate(axes)}

    # Hand-specified cohorts override generation
    if demo_cfg.cohorts:
        return _build_explicit_cohorts(demo_cfg, config.parties, axes, axis_idx)

    is_agents = demo_cfg.mode == "agents"
    cohorts_per_region = demo_cfg.cohorts_per_region if not is_agents else max(1, demo_cfg.n_agents // len(territory.regions))

    sizes_list: list[float] = []
    positions_list: list[np.ndarray] = []
    salience_list: list[np.ndarray] = []
    cov_list: list[np.ndarray] = []
    turnout_list: list[float] = []
    media_list: list[float] = []
    loyalty_list: list[np.ndarray] = []
    region_ids_list: list[str] = []
    attrs_list: list[dict[str, str]] = []

    m_parties = len(config.parties)
    party_indices = {p.id: i for i, p in enumerate(config.parties)}

    # Base ideology vector in [-1, 1]
    base_ideology_vec = np.zeros(n_dim, dtype=np.float64)
    for axis, val in demo_cfg.base_ideology.items():
        if axis in axis_idx:
            base_ideology_vec[axis_idx[axis]] = val / 100.0

    # Marginals & dimensions
    dimensions = demo_cfg.dimensions
    marginals = demo_cfg.marginals
    loadings = demo_cfg.loadings

    spread_scale = demo_cfg.ideology_spread / 100.0
    within_scale = (demo_cfg.within_spread / 100.0) if not is_agents else 0.01

    for reg_id, region in territory.regions.items():
        k = cohorts_per_region
        # Cohort sizes via Dirichlet distribution
        dirichlet_alpha = np.ones(k) * 2.0
        shares = rng.dirichlet(dirichlet_alpha)
        region_sizes = shares * region.population

        for c_idx in range(k):
            size = float(region_sizes[c_idx])
            sizes_list.append(size)
            region_ids_list.append(reg_id)

            # Sample attributes
            cohort_attrs: dict[str, str] = {}
            for dim in dimensions:
                dim_id = dim.id
                vals = dim.values
                # Region-adjusted marginal weights
                if dim_id in marginals and marginals[dim_id]:
                    probs = np.array([marginals[dim_id].get(v, 1.0 / len(vals)) for v in vals], dtype=np.float64)
                else:
                    probs = np.ones(len(vals), dtype=np.float64)

                # Regional conditional adjustments
                if dim_id == "settlement":
                    probs = np.array([region.urbanization, 1.0 - region.urbanization])
                elif dim_id == "education":
                    probs[2] *= (0.5 + region.education)
                elif dim_id == "religion":
                    probs[1] *= (0.5 + region.religiosity)
                elif dim_id == "identity":
                    probs[1] *= (0.5 + region.minority_share)

                probs = probs / np.sum(probs)
                chosen_val = str(rng.choice(vals, p=probs))
                cohort_attrs[dim_id] = chosen_val

            attrs_list.append(cohort_attrs)

            # Compute mean ideology shift from attribute loadings
            ideology_shift = np.zeros(n_dim, dtype=np.float64)
            for dim_id, val in cohort_attrs.items():
                attr_key = f"{dim_id}:{val}"
                if attr_key in loadings:
                    for axis, shift in loadings[attr_key].items():
                        if axis in axis_idx:
                            ideology_shift[axis_idx[axis]] += shift / 100.0

            # Add random cohort-specific perturbation
            perturb = rng.normal(0.0, spread_scale, size=n_dim)
            cohort_pos = np.clip(base_ideology_vec + ideology_shift + perturb, -1.0, 1.0)
            positions_list.append(cohort_pos)

            # Issue salience
            salience_vec = np.clip(rng.uniform(0.3, 0.8, size=n_dim) + 0.1 * np.abs(cohort_pos), 0.1, 1.0)
            salience_list.append(salience_vec)

            # Ideology covariance matrix (D x D)
            var_diag = np.full(n_dim, within_scale**2, dtype=np.float64)
            cov_matrix = np.diag(var_diag)
            cov_list.append(cov_matrix)

            # Turnout propensity (influenced by age, education, and baseline)
            base_turnout = 0.65
            if cohort_attrs.get("education") == "tertiary":
                base_turnout += 0.10
            elif cohort_attrs.get("education") == "primary":
                base_turnout -= 0.08
            if cohort_attrs.get("age") == "18-29":
                base_turnout -= 0.10
            elif cohort_attrs.get("age") == "65+":
                base_turnout += 0.10
            turnout_val = float(np.clip(rng.normal(base_turnout, 0.05), 0.2, 0.95))
            turnout_list.append(turnout_val)

            # Media susceptibility
            media_val = float(np.clip(rng.normal(0.5, 0.15), 0.1, 0.9))
            media_list.append(media_val)

            # Party brand loyalty / partisan identification
            loyalty_vec = np.zeros(m_parties, dtype=np.float64)
            for p in config.parties:
                p_idx = party_indices[p.id]
                # Check base appeal matches
                match_score = 0.0
                for dim_id, val in cohort_attrs.items():
                    key = f"{dim_id}:{val}"
                    if key in p.base_appeal:
                        match_score += p.base_appeal[key]
                loyalty_vec[p_idx] = float(np.clip(0.15 + 0.25 * match_score + rng.normal(0.0, 0.05), 0.0, 0.85))
            loyalty_list.append(loyalty_vec)

    return CohortState(
        sizes=np.array(sizes_list, dtype=np.float64),
        positions=np.array(positions_list, dtype=np.float64),
        baselines=np.array(positions_list, dtype=np.float64).copy(),
        salience=np.array(salience_list, dtype=np.float64),
        covariances=np.array(cov_list, dtype=np.float64),
        turnout=np.array(turnout_list, dtype=np.float64),
        loyalty=np.array(loyalty_list, dtype=np.float64),
        media=np.array(media_list, dtype=np.float64),
        region_ids=region_ids_list,
        attrs=attrs_list,
    )


def _build_explicit_cohorts(
    demo_cfg: DemographicsConfig,
    parties: list[PartyConfig],
    axes: list[str],
    axis_idx: dict[str, int],
) -> CohortState:
    assert demo_cfg.cohorts is not None
    n = len(demo_cfg.cohorts)
    n_dim = len(axes)
    m = len(parties)
    party_indices = {p.id: i for i, p in enumerate(parties)}

    sizes = np.zeros(n, dtype=np.float64)
    positions = np.zeros((n, n_dim), dtype=np.float64)
    salience = np.full((n, n_dim), 0.5, dtype=np.float64)
    covariances = np.zeros((n, n_dim, n_dim), dtype=np.float64)
    turnout = np.zeros(n, dtype=np.float64)
    media = np.zeros(n, dtype=np.float64)
    loyalty = np.zeros((n, m), dtype=np.float64)
    region_ids: list[str] = []
    attrs: list[dict[str, str]] = []

    for i, c in enumerate(demo_cfg.cohorts):
        sizes[i] = c.size
        region_ids.append(c.region)
        attrs.append(c.attrs)
        turnout[i] = c.turnout
        media[i] = c.media

        for axis, val in c.ideology.items():
            if axis in axis_idx:
                positions[i, axis_idx[axis]] = val / 100.0

        for axis, s in c.salience.items():
            if axis in axis_idx:
                salience[i, axis_idx[axis]] = s

        var_val = (c.spread / 100.0) ** 2
        covariances[i] = np.diag(np.full(n_dim, var_val))

        for pid, loy in c.loyalty.items():
            if pid in party_indices:
                loyalty[i, party_indices[pid]] = loy

    return CohortState(
        sizes=sizes,
        positions=positions,
        baselines=positions.copy(),
        salience=salience,
        covariances=covariances,
        turnout=turnout,
        loyalty=loyalty,
        media=media,
        region_ids=region_ids,
        attrs=attrs,
    )
