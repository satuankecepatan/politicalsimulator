"""Party strategic AI: repositioning (vote-, policy-, and office-seeking), cohesion, funding."""

from __future__ import annotations

import numpy as np

from polsim.config.schema import PartyParams
from polsim.core.mathx import clamp
from polsim.engine.state import CohortState, PartyState, RelationsState


def adapt_parties(
    parties: list[PartyState],
    cohorts: CohortState,
    relations: RelationsState,
    params: PartyParams,
    tick: int,
    rng: np.random.Generator,
) -> list[str]:
    """Execute party strategic repositioning, cohesion updates, and resource adjustments.

    Returns:
        List of human-readable log messages describing notable party moves or shifts.
    """
    logs: list[str] = []
    if tick % params.reposition_every != 0:
        return logs

    m = len(parties)
    if m == 0:
        return logs

    # Overall voter population center of mass (weighted by cohort sizes)
    total_pop = np.sum(cohorts.sizes)
    if total_pop > 0:
        voter_median = np.sum(cohorts.sizes[:, None] * cohorts.positions, axis=0) / total_pop
    else:
        voter_median = np.zeros(cohorts.positions.shape[1], dtype=np.float64)

    for i, party in enumerate(parties):
        if not party.active:
            continue

        # 1. Vote-seeking force: pull toward voter distribution centroid / median
        vote_seeking_dir = voter_median - party.position

        # 2. Policy-seeking force: pull back toward internal factions
        if party.factions:
            faction_ideal = np.zeros_like(party.position)
            total_weight = sum(f.weight for f in party.factions)
            for f in party.factions:
                faction_ideal += (f.weight / total_weight) * (party.position + f.offset)
            policy_seeking_dir = faction_ideal - party.position
        else:
            policy_seeking_dir = np.zeros_like(party.position)

        # 3. Office-seeking force: pull toward friendly potential coalition partners
        office_seeking_dir = np.zeros_like(party.position)
        friendly_partners = [
            j for j in range(m)
            if j != i and parties[j].active and relations.trust[i, j] > 0.6 and relations.hostility[i, j] < 0.3
        ]
        if friendly_partners:
            partner_positions = np.array([parties[j].position for j in friendly_partners])
            partner_centroid = np.mean(partner_positions, axis=0)
            office_seeking_dir = partner_centroid - party.position

        # Combine weighted forces
        combined_dir = (
            params.vote_seeking * vote_seeking_dir
            + params.policy_seeking * policy_seeking_dir
            + params.office_seeking * office_seeking_dir
        )

        # Bounded by pragmatism: maximum step size = max_step * pragmatism
        step_budget = params.max_step * max(0.1, party.pragmatism)
        norm = float(np.linalg.norm(combined_dir))
        if norm > 1e-5:
            step = (combined_dir / norm) * min(norm, step_budget)
            party.position = clamp(party.position + step, -1.0, 1.0)

        # 4. Update Internal Cohesion:
        # Distance from leadership position to furthest internal faction
        if party.factions:
            max_faction_dist = max(float(np.linalg.norm(f.offset)) for f in party.factions)
            # Higher distance -> lower cohesion
            party.cohesion = float(np.clip(1.0 - 0.7 * max_faction_dist, 0.05, 0.95))

        # 5. Funding and Organization updates
        # Successful parties gain funding; scandal or low vote share reduces funding
        target_funding = float(np.clip(party.vote_share * 2.0 + party.organization * 0.4 - party.scandal_accum * 0.3, 0.1, 0.95))
        party.funding += 0.05 * (target_funding - party.funding)

        # Natural scandal dissipation
        party.scandal_accum = max(0.0, party.scandal_accum - 0.02)
        # Temporary valence boost dissipation
        party.valence_boost = max(0.0, party.valence_boost - 0.05)

    return logs
